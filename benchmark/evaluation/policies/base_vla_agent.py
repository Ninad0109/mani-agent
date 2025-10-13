"""
Abstract Base Class for VLA Agent, Defines Unified Interface and Common Functions
"""

import json
from abc import ABC, abstractmethod
from collections import deque
from typing import Any, Optional
import numpy as np
import requests
from omegaconf import OmegaConf

from .adaptive_ensemble import AdaptiveEnsembler




class BaseVLAAgent(ABC):
    """
    Abstract Base Class for VLA Agent
    
    Attributes:
        base_url (str): Base URL for VLA service
        temperature (float): Generation temperature parameter
        replan_step (int): Replanning step count
        use_delta (bool): Whether to use delta mode
        current_step (int): Current step count
        last_act (Optional[np.ndarray]): Previous action
        action_queue (deque): Action queue
        action_ensembler (Optional[AdaptiveEnsembler]): Action ensemble
    """
    
    def __init__(self, config):
        """
        Initialize VLA agent
        
        Args:
            config: Loaded OmegaConf object
        """
        
        # Basic configuration
        self.base_url = config.base_url
        self.temperature = getattr(config, 'temperature', 1.0)
        self.replan_step = config.replan_step
        self.use_delta = getattr(config, 'use_delta', False)
        
        # State variables
        self.current_step = 0
        self.last_act = None
        self.action_queue = deque()
        
        # Action ensemble configuration
        self.action_ensemble_horizon = getattr(config, 'action_ensemble_horizon', 7)
        self.adaptive_ensemble_alpha = getattr(config, 'adaptive_ensemble_alpha', 0.1)
        
        # Initialize action ensemble
        if getattr(config, 'action_ensemble', False):
            self.action_ensembler = AdaptiveEnsembler(
                self.action_ensemble_horizon, 
                self.adaptive_ensemble_alpha
            )
        else:
            self.action_ensembler = None
            
        # Call subclass-specific initialization
        self._init_specific_config(config)

    @abstractmethod
    def _init_specific_config(self, config: OmegaConf) -> None:
        """
        Subclass-specific configuration initialization
        
        Args:
            config (OmegaConf): Configuration object
        """
        pass

    def reset(self) -> None:
        """
        Reset agent state
        
        Clear current step count, previous action, action queue, and ensemble state.
        """
        self.current_step = 0
        self.last_act = None
        self.action_queue.clear()
        
        if self.action_ensembler is not None:
            self.action_ensembler.reset()

    @abstractmethod
    def step(self, obs: Any, goal: str) -> Any:
        """
        Execute one step of inference
        
        Args:
            obs: Environment observation
            goal (str): Goal description
            
        Returns:
            Predicted action
        """
        pass

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
    def _add_new_action(self, obs: Any, goal: str) -> None:
        """
        Add new action to queue
        
        This method processes observation data, calls VLA service to get action predictions,
        and adds processed actions to the queue.
        
        Args:
            obs: Environment observation
            goal (str): Goal description
        """
        # Prepare state information
        state = self._prepare_state(obs)
        
        # Prepare image data
        images = self._prepare_images(obs)

        # # prepare depth data
        # depth = self._prepare_depth(obs)
        
        # Call VLA service
        raw_actions = self._call_vla_service(images, goal, state)
        
        # Process action predictions
        self._process_action_predictions(raw_actions)

    @abstractmethod
    def _prepare_state(self, obs: Any) -> np.ndarray:
        """
        Prepare state information
        
        Args:
            obs: Environment observation
            
        Returns:
            np.ndarray: Processed state information
        """
        pass
    # @abstractmethod
    # def _prepare_depth(self, obs: Any) -> np.ndarray:
    #     """
    #     Prepare state information
        
    #     Args:
    #         obs: Environment observation
            
    #     Returns:
    #         np.ndarray: Processed state information
    #     """
    #     pass

    @abstractmethod
    def _prepare_images(self, obs: Any) -> list:
        """
        Prepare image data
        
        Args:
            obs: Environment observation
            
        Returns:
            list: Encoded image list
        """
        pass

    def _call_vla_service(self, images: list, goal: str, state: np.ndarray) -> np.ndarray:
        """
        Call VLA service to get action predictions
        
        Args:
            images (list): Encoded image list
            goal (str): Goal description
            state (np.ndarray): State information
            
        Returns:
            np.ndarray: Raw action predictions
            
        Raises:
            SystemExit: Exits program when VLA service does not return valid response
        """
        text = f'What action should the robot take to {goal}?'
        
        # Prepare request data (specific parameters determined by subclass)
        data = self._prepare_request_data(text, state)
        
    
        # Send request
        ret = requests.post(
            self.base_url + "/process_frame",
            data=data,
            files=[("image", img) for img in images],
        )
        
        # Check if request was successful
        ret.raise_for_status()
        
        # Parse response
        response_data = ret.json()
        response = response_data.get('response')
        
        # Check if response is valid
        if response is None:
            print(f"Error: VLA service did not return valid response. Response data: {response_data}")
            raise SystemExit("VLA service response invalid, exiting program")
            
        return response

    def _prepare_request_data(self, text: str, state: np.ndarray) -> dict:
        """
        Prepare request data, subclasses can override this method to customize parameters
        
        Args:
            text (str): Request text
            state (np.ndarray): State information
            
        Returns:
            dict: Request data dictionary
        """
        data = {"text": text}
        
        # If state information exists, add to request
        if state is not None:
            data["states"] = json.dumps(state.tolist())
            
        return data

    @abstractmethod
    def _process_action_predictions(self, raw_actions: list) -> None:
        """
        Process action predictions
        
        Perform ensemble processing on raw action predictions and generate actions
        for multiple time steps. Subclasses need to implement specific processing logic.
        
        Args:
            raw_actions (list): Raw action predictions
        """
        pass