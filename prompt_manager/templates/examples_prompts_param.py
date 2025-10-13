EXAMPLE_PROMPTS = {
    "default": """Here is an EXAMPLE
    You are a robotic assistant. Based on the task description, generate a control plan IN JSON FORMAT.
    Task: "put the banana on the plate"
    
    Input:
    {
        "task_description": "put the banana on the plate",
        "scene_info": {
            "objects": [
                {
                    "confidence": 0.814,
                    "object_name": "banana",
                    "position_3d_baselink": {
                        "x": 0.214,
                        "y": -0.102,
                        "z": 0.016,
                        "orientation_rpy":[-0.874, 1.56, 0],
                        "grasp_x": 0.217,
                        "grasp_y": -0.092,
                        "grasp_z": 0.015
                    }
                },
                {
                    "confidence": 0.630,
                    "object_name": "plate",
                    "position_3d_baselink": {
                        "x": 0.207,
                        "y": 0.139,
                        "z": -0.004,
                        "orientation_rpy":[0.560, 1.56, 0.480],
                        "grasp_x": 0.223,
                        "grasp_y": 0.141,
                        "grasp_z": -0.005
                        }
                    
                }
            ]
        }
    }

    Example control plan:
    {
        "control_plan": {
            "sequence": [
                [0.217, -0.092, 0.215, 0, 1.56, 0, 1],
                [0.217, -0.092, 0.215, -0.874, 1.56, 0, 1],
                [0.217, -0.092, 0.015, -0.874, 1.56, 0, 1],
                [0.217, -0.092, 0.015, -0.874, 1.56, 0, 0],
                [0.217, -0.092, 0.215, -0.874, 1.56, 0, 0],
                [0.217, -0.092, 0.215, 0, 1.56, 0, 0],
                [0.207, 0.139, 0.196, 0, 1.56, 0, 0],
                [0.207, 0.139, -0.004, 0, 1.56, 0, 0],
                [0.207, 0.139, -0.004, 0, 1.56, 0, 1],
                [0.207, 0.139, 0.196, 0, 1.56, 0, 1]
            ],
            "steps_description": [
                "Move to the top of the banana and open the gripper.",
                "Rotate the gripper to the grasping pose for the banana.",
                "Move to the banana and open the gripper.",
                "Close the gripper.",
                "Move to position above the banana and close the gripper.",
                "Rotate the gripper back to its initial pose for placement.",
                "Move to position above the plate and keep closing the gripper.",
                "Lower the banana slowly to the plate.",
                "Open the gripper, let the banana fall on the plate.",
                "Move to position above the plate and keep a safe distance."
            ],
            "sequence_param": "[
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"]+0.2,
                    0, 1.56, 0, 
                    1
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"]+0.2,
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    1
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    1
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    0
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"]+0.2,
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    0
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"]+0.2,
                    0, 1.56, 0,
                    0
                ],
                [
                    scene_info["objects"][1]["position_3d_baselink"]["x"],
                    scene_info["objects"][1]["position_3d_baselink"]["y"], 
                    scene_info["objects"][1]["position_3d_baselink"]["z"]+0.2,
                    0, 1.56, 0,
                    0
                ],
                [
                    scene_info["objects"][1]["position_3d_baselink"]["x"],
                    scene_info["objects"][1]["position_3d_baselink"]["y"], 
                    scene_info["objects"][1]["position_3d_baselink"]["z"],
                    0, 1.56, 0,
                    0
                ],
                [
                    scene_info["objects"][1]["position_3d_baselink"]["x"],
                    scene_info["objects"][1]["position_3d_baselink"]["y"], 
                    scene_info["objects"][1]["position_3d_baselink"]["z"],
                    0, 1.56, 0,
                    1
                ],
                [
                    scene_info["objects"][1]["position_3d_baselink"]["x"],
                    scene_info["objects"][1]["position_3d_baselink"]["y"], 
                    scene_info["objects"][1]["position_3d_baselink"]["z"]+0.2,
                    0, 1.56, 0,
                    1
                ]
            ]",
        }
    }

    Input:
    {
        "task_description": "put the bowl on [0.3, 0.1, 0.02, 1.2, 1.56, 0]([x, y, z, roll, pitch, yaw])",# When manipulating objects such as bowls or plates, the gripper does not have enough force to grab, so the object is dragged to the specified position by going to the center of the object and dragging it.
        "scene_info": {
            "objects": [
                {
                    "confidence": 0.630,
                    "object_name": "bowl",
                    "position_3d_baselink": {
                        "x": 0.207,
                        "y": 0.139,
                        "z": 0.004,
                        "orientation_rpy":[0.560, 1.56, 0.480],
                        "grasp_x": 0.223,
                        "grasp_y": 0.141,
                        "grasp_z": -0.005
                        }
                    
                }
            ]
        }
    }

    Example control plan:
    {
        "control_plan": {
            "sequence": [
                [0.207, 0.139, 0.204, 0, 1.56, 0, 1],
                [0.207, 0.139, 0.004, 0, 1.56, 0, 1],
                [0.3, 0.1, 0.02, 0, 1.56, 0, 1],
                [0.3, 0.1, 0.22, 0, 1.56, 0, 1]
            ],
            "steps_description": [
                "Move to the top of the bowl and open the gripper.",
                "Move to the bowl and open the gripper.",
                "Drag the bowl to the target location.",
                "Move to position above the bowl and keep a safe distance."
            ],
            "sequence_param": "[
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"]+0.2,
                    0, 1.56, 0, 
                    1
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"],
                    0, 1.56, 0, 
                    1
                ],
                [
                    target_x,
                    target_y, 
                    target_z,
                    0, 1.56, 0, 
                    1
                ],
                [
                    target_x,
                    target_y, 
                    target_z+0.2,
                    0, 1.56, 0, 
                    1
                ]
            ]"
        }
    }

    Input:
    {
        "task_description": "put the banana on [0.207, 0.139, -0.004, 1.0, 1.56, 0,]([x, y, z, roll, pitch, yaw])",# When manipulating objects such as bowls or plates, the gripper does not have enough force to grab, so the object is dragged to the specified position by going to the center of the object and dragging it.
        "scene_info": {
            "objects": [
                {
                    "confidence": 0.814,
                    "object_name": "banana",
                    "position_3d_baselink": {
                        "x": 0.214,
                        "y": -0.102,
                        "z": 0.016,
                        "orientation_rpy":[-0.874, 1.56, 0],
                        "grasp_x": 0.217,
                        "grasp_y": -0.092,
                        "grasp_z": 0.015
                    }
                }
            ]
        }
    }

    Example control plan:
    {
        "control_plan": {
            "sequence": [
                [0.217, -0.092, 0.215, 0, 1.56, 0, 1],
                [0.217, -0.092, 0.215, -0.874, 1.56, 0, 1],
                [0.217, -0.092, 0.015, -0.874, 1.56, 0, 1],
                [0.217, -0.092, 0.015, -0.874, 1.56, 0, 0],
                [0.217, -0.092, 0.215, -0.874, 1.56, 0, 0],
                [0.217, -0.092, 0.215, 1.0, 1.56, 0, 0],
                [0.207, 0.139, 0.196, 1.0, 1.56, 0, 0],
                [0.207, 0.139, -0.004, 1.0, 1.56, 0, 0],
                [0.207, 0.139, -0.004, 1.0, 1.56, 0, 1],
                [0.207, 0.139, 0.196, 1.0, 1.56, 0, 1]
            ],
            "steps_description": [
                "Move to the top of the banana and open the gripper.",
                "Rotate the gripper to the grasping pose for the banana.",
                "Move to the banana and open the gripper.",
                "Close the gripper.",
                "Move to position above the banana and close the gripper.",
                "Rotate the gripper back to its initial pose for placement.",
                "Move to position above the target and keep closing the gripper.",
                "Lower the banana slowly to the target.",
                "Open the gripper, let the banana fall on the target.",
                "Move to position above the target and keep a safe distance."
            ],
            "sequence_param": "[
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"]+0.2,
                    0, 1.56, 0, 
                    1
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"]+0.2,
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    1
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    1
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    0
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"]+0.2,
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    0
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_x"],
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["grasp_z"]+0.2,
                    target_roll, target_pitch, target_yaw,
                    0
                ],
                [
                    scene_info["objects"][1]["position_3d_baselink"]["x"],
                    scene_info["objects"][1]["position_3d_baselink"]["y"], 
                    scene_info["objects"][1]["position_3d_baselink"]["z"]+0.2,
                    target_roll, target_pitch, target_yaw,
                    0
                ],
                [
                    scene_info["objects"][1]["position_3d_baselink"]["x"],
                    scene_info["objects"][1]["position_3d_baselink"]["y"], 
                    scene_info["objects"][1]["position_3d_baselink"]["z"],
                    target_roll, target_pitch, target_yaw,
                    0
                ],
                [
                    scene_info["objects"][1]["position_3d_baselink"]["x"],
                    scene_info["objects"][1]["position_3d_baselink"]["y"], 
                    scene_info["objects"][1]["position_3d_baselink"]["z"],
                    target_roll, target_pitch, target_yaw,
                    1
                ],
                [
                    scene_info["objects"][1]["position_3d_baselink"]["x"],
                    scene_info["objects"][1]["position_3d_baselink"]["y"], 
                    scene_info["objects"][1]["position_3d_baselink"]["z"]+0.2,
                    target_roll, target_pitch, target_yaw,
                    1
                ]
            ]",
        }
    }

    Input:
    {
        "task_description": "Unscrew the bottle cap",# When performing rotation tasks, you can add or subtract numbers on roll, pitch, and yaw. Rotation on the xy plane can be achieved by adding or subtracting the roll value (for example, unscrew a bottle cap), and rotation on the xz plane can be achieved by adding or subtracting the pitch value (for example, pouring water).
        "scene_info": {
            "objects": [
                {
                    "confidence": 0.630,
                    "object_name": "bottle cap",
                    "position_3d_baselink": {
                        "x": 0.326,
                        "y": 0.212,
                        "z": 0.104,
                        "orientation_rpy":[0.560, 1.56, 0.0],
                        "grasp_x": 0.350,
                        "grasp_y": 0.202,
                        "grasp_z": 0.094
                        }
                    
                }
            ]
        }
    }

    Example control plan:
    {
        "control_plan": {
            "sequence": [
                [0.326, 0.212, 0.204, 0.560, 1.56, 0.0, 1],
                [0.326, 0.212, 0.104, 0.560, 1.56, 0.0, 1],
                [0.326, 0.212, 0.104, 0.560, 1.56, 0.0, 0],
                [0.326, 0.212, 0.104, 0.060, 1.56, 0.0, 0],
                [0.326, 0.212, 0.104, 0.060, 1.56, 0.0, 1],
                [0.326, 0.212, 0.104, 0.560, 1.56, 0.0, 1],
                [0.326, 0.212, 0.104, 0.560, 1.56, 0.0, 0],
                [0.326, 0.212, 0.104, 0.060, 1.56, 0.0, 0],
                [0.326, 0.212, 0.204, 0.060, 1.56, 0.0, 0],
                [0.326, 0.212, 0.204, 0.060, 1.56, 0.0, 1]
            ],
            "steps_description": [
                "Move to the top of the bottle and open the gripper.",
                "Move to the bottle cap and open the gripper.",
                "Move to the bottle cap and close the gripper.",
                "Rotate the bottle cap counterclockwise 0.5 (radians).",
                "Open the gripper.",
                "Rotate to grasping posture",
                "Close the gripper.",
                "Rotate the bottle cap counterclockwise 0.5 (radians).",
                "Move to position above the bottle and keep a safe distance.",
                "Open the gripper, let the bottle cap fall"
            ],
            "sequence_param": "[
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"]+0.1,
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    1
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    1
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    0
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0]-0.5, 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    0
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0]-0.5, 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    1
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    1
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    0
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0]-0.5, 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    0
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"]+0.1,
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0]-0.5, 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    0
                ],
                [
                    scene_info["objects"][0]["position_3d_baselink"]["x"],
                    scene_info["objects"][0]["position_3d_baselink"]["y"], 
                    scene_info["objects"][0]["position_3d_baselink"]["z"]+0.1,
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][0], 
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][1],
                    scene_info["objects"][0]["position_3d_baselink"]["orientation_rpy"][2],
                    1
                ],
            ]"
        }
    }


    
    Remember: Always generate a COMPLETE sequence with multiple movements!
    NOTE that you should use the grasping positions grasp_x, grasp_y, grasp_z as much as possible. 
    This position is more accurate than the detected position.
    """,
    'detection_request':"""
    Here are some EXAMPLES
    Input:
    {
        "task_description": "put the banana on the plate",
    }
    Output:
    {
        "object_to_detect": ['banana','plate'],
    }
    
    Input:
    {
        "task_description": "put the banana on [0.1, 0.2, 0.3, 1.0, 1.56, 0]([x, y, z, roll, pitch, yaw])",
    }
    Output:
    {
        "object_to_detect": ['banana'],
    }
    
    """
}
