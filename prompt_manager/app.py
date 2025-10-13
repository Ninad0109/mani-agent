# prompt_manager/app.py
from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
import sys

# Add project root directory to path to import templates
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt_manager.templates.system_prompts_param import SYSTEM_PROMPTS
from prompt_manager.templates.task_prompts_param import TASK_TEMPLATES
from prompt_manager.templates.examples_prompts_param import EXAMPLE_PROMPTS

app = Flask(__name__)

# Create log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

class PromptManager:
    def __init__(self):
        self.system_prompts = SYSTEM_PROMPTS
        self.task_templates = TASK_TEMPLATES
        self.example_prompts = EXAMPLE_PROMPTS
    
    def format_3d_scene(self, objects):
        """Format 3D scene information to JSON format"""
        scene_desc = []
        for obj in objects:
            if 'position_3d_baselink' in obj:
                pos_3d = obj['position_3d_baselink']
                scene_desc.append({
                    "object_name": obj['object_name'],
                    "position_3d_baselink": {
                        "x": pos_3d.get('x', 0),
                        "y": pos_3d.get('y', 0),
                        "z": pos_3d.get('z', 0),
                        "orientation_rpy": pos_3d.get('orientation_rpy'),
                        "grasp_x": pos_3d.get('grasp_x', 0),
                        "grasp_y": pos_3d.get('grasp_y', 0),
                        "grasp_z": pos_3d.get('grasp_z', 0),
                    },
                    "confidence": obj.get('confidence', 0)
                })
            else:
                # No 3D information, use 2D information
                center = obj['center_position']
                scene_desc.append({
                    "object_name": obj['object_name'],
                    "position": {
                        "x": center['x'],
                        "y": center['y']
                    },
                    "confidence": obj.get('confidence', 0)
                })
        return scene_desc

    def build_prompt(self, task_desc: str, scene_info: dict, task_type: str = 'default') -> dict:
        """Build complete prompt"""
        # Select system prompt
        system_prompt = self.system_prompts.get(task_type, self.system_prompts['default'])
        
        # Select task template
        task_template = self.task_templates.get(task_type, self.task_templates['default'])

        # Select example template
        example_prompts = self.example_prompts.get(task_type, self.example_prompts['default'])
        
        # Process scene information
        objects = scene_info.get('objects', [])
        scene_description = self.format_3d_scene(objects) if objects else []
            
        # Fill task template
        task_prompt = task_template.format(
            task_description=task_desc,
            scene_description=json.dumps(scene_description)  
        )

        # Build final message list
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_prompt},
            {"role": "user", "content": example_prompts},
        ]
        
        return {
            "messages": messages
        }

    def save_prompt_log(self, prompt: dict, task_desc: str, scene_info: dict, task_type: str):
        """Save prompt log"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prompt_{timestamp}.json"
        filepath = os.path.join(LOG_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "task_description": task_desc,
                "task_type": task_type,
                "scene_info": scene_info,
                "prompt": prompt
            }, f, indent=2)
        
        print(f"Saved prompt log to: {filepath}")
        return filepath

prompt_manager = PromptManager()

@app.route('/build_prompt', methods=['POST'])
def build_prompt():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        task_desc = data.get('task_description')
        scene_info = data.get('scene_info', {})
        task_type = data.get('task_type', 'default')
        
        if not task_desc:
            return jsonify({"error": "Missing task description"}), 400
            
        prompt = prompt_manager.build_prompt(task_desc, scene_info, task_type)
        
        # Save log
        log_path = prompt_manager.save_prompt_log(prompt, task_desc, scene_info, task_type)
        
        # Add metadata to response
        response = {
            "prompt": prompt,
            "metadata": {
                "task_type": task_type,
                "log_path": log_path,
                "object_count": len(scene_info.get('objects', []))
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error building prompt: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "available_task_types": list(SYSTEM_PROMPTS.keys())
    })

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=4599, help="Port to run the prompt service on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=False)
