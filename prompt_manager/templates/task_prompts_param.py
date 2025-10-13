# prompt_manager/templates/task_prompts.py
TASK_TEMPLATES = {
    'default': """Task Description: {task_description}

Current Scene:
{scene_description}

When grasping the object being manipulated, "grasp_x", "grasp_y", "grasp_z" can replace "x", "y", "z"; as "grasp_x", "grasp_y", "grasp_z" are more precise, their use is recommended.
When operating objects that are not easy to grasp, such as bowls and plates, please refer to the example for bowl operation to generate actions. Do not use the grasping strategy, but the dragging strategy.

Generate a detailed control sequence to accomplish this task.
Break down the task into clear steps and provide the exact movement commands.
Ensure all movements are safe and collision-free.
Note that if the input is in the form of "place the object at [x, y, z, roll, pitch, yaw]", please use this posture as the target posture directly.

Return your response IN JSON FORMAT with the following structure:
{{
    "sequence": [
        [x, y, z, roll, pitch, yaw, gripper],  // Each movement step
        [x, y, z, roll, pitch, yaw, gripper],  // Each movement step
        [x, y, z, roll, pitch, yaw, gripper],  // Each movement step
        [x, y, z, roll, pitch, yaw, gripper],  // Each movement step
        [x, y, z, roll, pitch, yaw, gripper],  // Each movement step
        ...
    ],
    "steps_description": [
        "Description of step 1",
        "Description of step 2",
        "Description of step 3",
        "Description of step 4",
        "Description of step 5",
        ...
    ],
    "sequence_param": "[[
    "scene_info["objects"][1]["position_3d_baselink"]["x"]",
    "scene_info["objects"][1]["position_3d_baselink"]["y"]",
    "scene_info["objects"][1]["position_3d_baselink"]["z"]",
    "scene_info["objects"][1]["position_3d_baselink"]["orientation_rpy"][0]",
    "scene_info["objects"][1]["position_3d_baselink"]["orientation_rpy"][1]",
    "scene_info["objects"][1]["position_3d_baselink"]["orientation_rpy"][2]",
    0(parameter descriptions for each action)
    ],
    ... (multiple actions)
    ]"
}}
-Notice: You MUST output sequence_param in str form because later I need to restore it back to a list using eval(sequence_param).
""",
}