"""
VLA Agent Implementation for Simpler Project
"""

from typing import Optional, Sequence, Tuple, Dict
from collections import deque
import requests

import numpy as np
import cv2
import matplotlib.pyplot as plt
from transforms3d.euler import euler2axangle
from omegaconf import OmegaConf

# from .base_vla_agent import BaseVLAAgent

from .adaptive_ensemble import AdaptiveEnsembler


import pickle

import io

import json

from scipy.spatial.transform import Rotation as R

class SimplerVLAAgent:
    def __init__(self, config):
        # config = OmegaConf.load(config)
        
        self.base_url = config.base_url
        self.use_delta = config.use_delta
        self.replan_step = config.replan_step
        self.image_size = (224, 224)  # default image size for resizing
        # assert self.use_delta, "VLAInference only supports delta mode"
        
        self.last_action = None
        self.action_queue = deque()
        
        self.action_ensemble_horizon = config.get('action_ensemble_horizon', 7)
        
        self.adaptive_ensemble_alpha = config.get('adaptive_ensemble_alpha', 0.1)
        self.action_ensembler = AdaptiveEnsembler(self.action_ensemble_horizon, self.adaptive_ensemble_alpha)
        
    def reset(self, task_description: str) -> None:
        self.action_queue.clear()
        self.action_ensembler.reset()
    
    def step(self, image: np.ndarray, depth: np.ndarray,camera_params, obs, task_description: Optional[str] = None) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
        """
        Input:
            image: np.ndarray of shape (H, W, 3), uint8
            depth: np.ndarray of shape (H, W), uint8
            camera_params
            task_description: Optional[str], task description; if different from previous task description, policy state is reset
        Output:
            raw_action: dict; raw policy action output
            action: dict; processed action to be sent to the maniskill2 environment, with the following keys:
                - 'world_vector': np.ndarray of shape (3,), xyz translation of robot end-effector
                - 'rot_axangle': np.ndarray of shape (3,), axis-angle representation of end-effector rotation
                - 'gripper': np.ndarray of shape (1,), gripper action
                - 'terminate_episode': np.ndarray of shape (1,), 1 if episode should be terminated, 0 otherwise
        """
        if len(self.action_queue) == 0:
            self.add_new_action(image, depth, camera_params, obs, task_description)
        
        action, raw_action = self.action_queue.popleft()

        return raw_action, action
    
    def _resize_image(self, image: np.ndarray) -> np.ndarray:
        image = cv2.resize(image, tuple(self.image_size), interpolation=cv2.INTER_AREA)
        return image


    def split_large_deltas(self, raw_actions, max_delta=0.03):
        """
        拆分过大的delta动作：当某个delta动作的分量绝对值超过max_delta时，
        将其拆分为多个小delta动作，确保总增量不变，且每个小步骤不超过阈值。
        
        参数:
            raw_actions: 原始delta动作数组，形状为(n, m)，每个动作是相对于前一状态的增量
            max_delta: 单个delta动作分量的最大允许值（绝对值）
        
        返回:
            split_actions: 拆分后的delta动作数组
        """
        split_actions = []
        
        for delta in raw_actions:
            # 检查前6个维度（假设是位置和旋转的delta）
            delta_pos_rot = delta[:6]
            # 计算每个分量的绝对值
            abs_deltas = np.abs(delta_pos_rot)
            # 找到最大绝对值超过阈值的分量
            max_abs = np.max(abs_deltas)
            
            if max_abs <= max_delta:
                # 无需拆分，直接添加
                split_actions.append(delta)
            else:
                # 计算需要拆分的步数（向上取整）
                steps = int(np.ceil(max_abs / max_delta))
                # 每个小步骤的delta（均匀分配）
                step_delta = delta.copy()
                step_delta[:6] = delta_pos_rot / steps  # 前6维拆分
                
                # 添加所有小步骤（共steps个，总和等于原始delta）
                for _ in range(steps):
                    split_actions.append(step_delta)
        
        return np.array(split_actions)
    
    def split_large_deltas_rot(self, raw_actions, max_delta_pos=0.03, max_delta_rot=0.3):
        """
        拆分过大的delta动作：对位置和旋转分量设置不同的最大步进阈值
        - 前3维（位置）单维最大步进为max_delta_pos（0.03）
        - 后3维（旋转）单维最大步进为max_delta_rot（0.3）
        
        参数:
            raw_actions: 原始delta动作数组，形状为(n, m)
            max_delta_pos: 位置分量（前3维）的最大允许步进
            max_delta_rot: 旋转分量（后3维）的最大允许步进
        
        返回:
            split_actions: 拆分后的delta动作数组
        """
        split_actions = []
        
        for delta in raw_actions:
            # 分离位置分量（前3维）和旋转分量（4-6维）
            delta_pos = delta[:3]
            delta_rot = delta[3:6]
            
            # 计算位置和旋转各分量的绝对值
            abs_pos = np.abs(delta_pos)
            abs_rot = np.abs(delta_rot)
            
            # 找到位置和旋转中需要的最大步数
            # 位置：超过max_delta_pos的分量所需步数
            pos_steps = [np.ceil(abs_p / max_delta_pos) for abs_p in abs_pos if abs_p > 0]
            # 旋转：超过max_delta_rot的分量所需步数
            rot_steps = [np.ceil(abs_r / max_delta_rot) for abs_r in abs_rot if abs_r > 0]
            
            # 确定总步数（取所有需要的最大步数，至少为1）
            all_steps = pos_steps + rot_steps
            steps = int(max(all_steps)) if all_steps else 1
            
            # 计算每个小步骤的delta
            step_delta = delta.copy()
            step_delta[:3] = delta_pos / steps  # 位置分量拆分
            step_delta[3:6] = delta_rot / steps  # 旋转分量拆分
            
            # 添加所有小步骤（总和等于原始delta）
            for _ in range(steps):
                split_actions.append(step_delta)
        
        return np.array(split_actions)
    
    def split_large_deltas_rot_keep_grasp(self, raw_actions, max_delta_pos=0.03, max_delta_rot=0.3):
        """
        拆分过大的delta动作：对位置和旋转分量设置不同的最大步进阈值
        - 前3维（位置）单维最大步进为max_delta_pos（0.03）
        - 后3维（旋转）单维最大步进为max_delta_rot（0.3）
        - 新增：当最后一维数值变化时，在变化的动作后添加两个相同的动作保持状态
        
        参数:
            raw_actions: 原始delta动作数组，形状为(n, m)
            max_delta_pos: 位置分量（前3维）的最大允许步进
            max_delta_rot: 旋转分量（后3维）的最大允许步进
        
        返回:
            split_actions: 拆分后的delta动作数组
        """
        split_actions = []
        # 记录上一个动作的最后一维值（初始为None）
        prev_last_dim = None
        
        for delta in raw_actions:
            # 分离位置分量（前3维）和旋转分量（4-6维）
            delta_pos = delta[:3]
            delta_rot = delta[3:6]
            # 获取最后一维的值
            current_last_dim = delta[-1]
            
            # 计算位置和旋转各分量的绝对值
            abs_pos = np.abs(delta_pos)
            abs_rot = np.abs(delta_rot)
            
            # 找到位置和旋转中需要的最大步数
            # 位置：超过max_delta_pos的分量所需步数
            pos_steps = [np.ceil(abs_p / max_delta_pos) for abs_p in abs_pos if abs_p > 0]
            # 旋转：超过max_delta_rot的分量所需步数
            rot_steps = [np.ceil(abs_r / max_delta_rot) for abs_r in abs_rot if abs_r > 0]
            
            # 确定总步数（取所有需要的最大步数，至少为1）
            all_steps = pos_steps + rot_steps
            steps = int(max(all_steps)) if all_steps else 1
            
            # 计算每个小步骤的delta
            step_delta = delta.copy()
            step_delta[:3] = delta_pos / steps  # 位置分量拆分
            step_delta[3:6] = delta_rot / steps  # 旋转分量拆分
            
            # 添加所有小步骤（总和等于原始delta）
            current_split = [step_delta.copy() for _ in range(steps)]
            split_actions.extend(current_split)
            
            # 检查最后一维是否发生变化（排除第一个动作）
            if prev_last_dim is not None and current_last_dim != prev_last_dim:
                # 创建保持动作：位置和旋转增量为0，仅保留最后一维的新值
                hold_action = np.zeros_like(delta)
                hold_action[-1] = current_last_dim  # 保持最后一维的新值
                # 添加两个保持动作
                split_actions.extend([hold_action.copy(), hold_action.copy()])
            
            # 更新上一个动作的最后一维值
            prev_last_dim = current_last_dim
        
        return np.array(split_actions)

    def add_new_action(self, image, depth, camera_params_raw, obs, goal):
        max_retries = 10
        retry_count = 0
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) 
        while retry_count < max_retries:
            try:
                enc_imgs = []
                depth_pickles = []
                camera_params = {
                    "intrinsics": [camera_params_raw.get('intrinsic_cv').tolist(),
                        camera_params_raw.get('intrinsic_cv').tolist()
                    ],
                    "extrinsics": [np.linalg.inv(camera_params_raw.get('extrinsic_cv')).tolist(),
                        np.linalg.inv(camera_params_raw.get('extrinsic_cv')).tolist()
                    ]
                }
                # image = self._resize_image(image) # 这里不resize image了，要不然内参对不上
                # if retry_count == 0:
                #     image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # convert to RGB format
                _, encoded_image = cv2.imencode('.png', image)
                img_bytes = encoded_image.tobytes()
                enc_imgs.append((
                        "front.png",    # e.g., 'front.png'
                        io.BytesIO(img_bytes)
                    ))
                enc_imgs.append((
                        "side.png",    # e.g., 'front.png'
                        io.BytesIO(img_bytes)
                    ))
                    
                
                depth_pickle_bytes = pickle.dumps(depth)
                depth_pickles.append((
                        f"front_depth.pkl",    # e.g., 'front_depth.pkl'
                        depth_pickle_bytes
                    ))
                depth_pickles.append((
                        f"side_depth.pkl",    # e.g., 'front_depth.pkl'
                        depth_pickle_bytes
                    ))
                text = f'{goal}'
                files = []
                for name, fileobj in enc_imgs:
                    files.append(('image', (name, fileobj, 'image/png')))

                for name, data in depth_pickles:
                    files.append(('depth', (name, data)))
                ret = requests.post(
                    self.base_url+"/process_frame",
                    data={"text": text, "camera_params": json.dumps(camera_params)},
                    files=files,
                )
                response = ret.json().get('response')
                raw_actions = np.array(response)
                raw_actions[:,-2] = -raw_actions[:,-4]
                raw_actions[:,-4] = 0
                raw_actions[:,:2] = obs['agent']['base_pose'][:2]-raw_actions[:,:2]
                raw_actions[:,2] = raw_actions[:,2]-obs['agent']['base_pose'][2]
                raw_actions_ori = raw_actions.copy()
                raw_actions[0,:3] -= obs['agent']['controller']['arm']['target_pose'][:3]
                raw_actions[0,3:-1] =[0,0,0]
                if raw_actions is not None:
                    break
                retry_count += 1
            except Exception as e:
                retry_count += 1
                print(f"Error occurred while sending request: {e}, retrying...")
                if retry_count == max_retries:
                    raise Exception(f"Failed to get valid response after {max_retries} retries. Last error: {str(e)}")
                continue
        # try:
        #     ret = requests.post(
        #             self.base_url+"/process_frame",
        #             data={"text": text, "camera_params": json.dumps(camera_params),},
        #             files=files
        #         )
        #     response = ret.json().get('response')
        # except:
        #     ret = requests.post(
        #             self.base_url+"/process_frame",
        #             data={"text": text, "camera_params": json.dumps(camera_params),},
        #             files=files
        #         )
        #     response = ret.json().get('response')
        # raw_actions = np.array(response)
        # raw_actions[:,-2] = -raw_actions[:,-4]
        # raw_actions[:,-4] = 0
        # raw_actions[:,:2] = obs['agent']['base_pose'][:2]-raw_actions[:,:2]
        # raw_actions[:,2] = raw_actions[:,2]-obs['agent']['base_pose'][2]
        # raw_actions_ori = raw_actions.copy()
        # raw_actions[0,:3] -= obs['agent']['controller']['arm']['target_pose'][:3]
        # raw_actions[0,3:-1] =[0,0,0]

        for i in range(1, len(raw_actions)):
            # 当前数组的前6个元素 = 自身前6个元素 - 前一个数组的前6个元素
            raw_actions[i, :6] -= raw_actions_ori[i-1, :6]
        # raw_actions = self.action_ensembler.ensemble_action(raw_actions)[None]
        # # debug用
        # raw_actions = raw_actions[[0]]
        # yangyi=1
        # 
        raw_actions = self.split_large_deltas_rot_keep_grasp(raw_actions, max_delta_pos=0.01, max_delta_rot=0.1)
        for i in range(len(raw_actions)):

            gripper = 2.0 * (raw_actions[i][6] > 0.5) - 1.0  # convert to [-1, 1] range
            
            rotation = raw_actions[i][3:6]
            axes, angles = euler2axangle(*rotation)
            action_rotation_axangle = axes * angles
            action = {
                'world_vector':np.array(raw_actions[i][:3]),
                'rot_axangle': np.array(action_rotation_axangle),
                'gripper': np.array([gripper]),
                'terminate_episode': np.zeros(1),
            }
            
            raw_action = {
                "world_vector": np.array(raw_actions[i][:3]),
                "rotation_delta": np.array(raw_actions[i][3:6]),
                "open_gripper": action['gripper'],
            }
            self.action_queue.append((action, raw_action))
            
    def visualize_epoch(self, predicted_raw_actions: Sequence[np.ndarray], images: Sequence[np.ndarray], save_path: str) -> None:
        images = [self._resize_image(image) for image in images]
        ACTION_DIM_LABELS = ["x", "y", "z", "roll", "pitch", "yaw", "grasp"]

        img_strip = np.concatenate(np.array(images[::3]), axis=1)

        # set up plt figure
        figure_layout = [["image"] * len(ACTION_DIM_LABELS), ACTION_DIM_LABELS]
        plt.rcParams.update({"font.size": 12})
        fig, axs = plt.subplot_mosaic(figure_layout)
        fig.set_size_inches([45, 10])

        # plot actions
        pred_actions = np.array(
            [
                np.concatenate([a["world_vector"], a["rotation_delta"], a["open_gripper"]], axis=-1)
                for a in predicted_raw_actions
            ]
        )
        for action_dim, action_label in enumerate(ACTION_DIM_LABELS):
            # actions have batch, horizon, dim, in this example we just take the first action for simplicity
            axs[action_label].plot(pred_actions[:, action_dim], label="predicted action")
            axs[action_label].set_title(action_label)
            axs[action_label].set_xlabel("Time in one episode")

        axs["image"].imshow(img_strip)
        axs["image"].set_xlabel("Time in one episode (subsampled)")
        plt.legend()
        plt.savefig(save_path)