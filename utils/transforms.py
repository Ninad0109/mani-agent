# utils/transforms.py
import numpy as np
from typing import List

def pixel_to_3d_baselink(x_pixel: float, y_pixel: float, depth_value: float, 
                         camera_intrinsics: List[List[float]], 
                         camera_extrinsics: List[List[float]]) -> List[float]:
    """
    将像素坐标转换为baselink坐标系下的3D位置
    :param x_pixel: 像素x坐标
    :param y_pixel: 像素y坐标
    :param depth_value: 深度值（米）
    :param camera_intrinsics: 相机内参矩阵 (3x3)
    :param camera_extrinsics: 相机外参矩阵 (4x4)
    :return: baselink坐标系下的3D位置 [x, y, z]
    """
    # 内参矩阵
    K = np.array(camera_intrinsics).reshape(3, 3)
    
    # 外参矩阵 (相机到baselink的变换)
    T_base_cam = np.array(camera_extrinsics).reshape(4, 4)
    
    # 相机坐标系下的3D点
    z_cam = depth_value
    x_cam = (x_pixel - K[0, 2]) * z_cam / K[0, 0]
    y_cam = (y_pixel - K[1, 2]) * z_cam / K[1, 1]
    
    # 相机坐标系下的点（齐次坐标）
    try:
        point_cam = np.array([x_cam, y_cam, z_cam, 1.0])
    except:
        point_cam = np.array([x_cam[0], y_cam[0], z_cam[0], 1.0])
    
    # 转换到baselink坐标系
    point_base = T_base_cam @ point_cam
    
    return point_base[:3].tolist()
