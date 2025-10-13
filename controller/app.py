# controller/app_dual_cam.py
from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime
from openai import OpenAI
import time

import base64
import pickle
import re

from PIL import Image
import io

app = Flask(__name__)

# Create log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ------------------------------
# Recording state constants
# ------------------------------
RECORDING_STATES = {
    "IDLE": "idle",           # Idle state
    "RECORDING": "recording"  # Recording state
}

TASK_CACHE = {}
OBJECT_CACHE = {}

from pathlib import Path
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "action_cache.json")
OBJECT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "object_cache.json")

def save_dict_to_json(data: dict, file_path: str, indent: int = 4, ensure_ascii: bool = False) -> bool:
    """
    Save dictionary to JSON file
    
    Args:
        data: Dictionary to save
        file_path: File path to save (e.g., "output/data.json")
        indent: JSON indentation spaces, 0 for no formatting
        ensure_ascii: Whether to ensure ASCII encoding (False preserves non-ASCII like Chinese)
    
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # Create parent directory if it doesn't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(
                data,
                f,
                indent=indent,
                ensure_ascii=ensure_ascii,
                sort_keys=False  # Do not sort keys, preserve original order
            )
        print(f"Dictionary saved successfully to: {file_path}")
        return True
    
    except TypeError as e:
        print(f"Save failed: Dictionary contains JSON-unsupported data types - {e}")
    except PermissionError:
        print(f"Save failed: No permission to write file {file_path}")
    except Exception as e:
        print(f"Save failed: Unknown error occurred - {e}")
    
    return False

def load_dict_from_json(file_path: str, default: dict = None) -> dict:
    """
    Load data from JSON file and convert to dictionary
    
    Args:
        file_path: JSON file path to read (e.g., "data/input.json")
        default: Default value to return if file doesn't exist or read fails (default empty dict)
    
    Returns:
        Dictionary if loaded successfully, default otherwise (empty dict by default)
    """
    if default is None:
        default = {}
    
    try:
        # Check if file exists
        if not Path(file_path).exists():
            print(f"Load failed: File does not exist - {file_path}")
            return default
        
        # Read JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verify result is a dictionary
        if not isinstance(data, dict):
            print(f"Load failed: File content is not a valid JSON dictionary - {file_path}")
            return default
        
        print(f"Dictionary loaded successfully from {file_path}")
        return data
    
    except json.JSONDecodeError as e:
        print(f"Load failed: JSON format error - {e}")
    except PermissionError:
        print(f"Load failed: No permission to read file {file_path}")
    except Exception as e:
        print(f"Load failed: Unknown error occurred - {e}")
    
    return default

try:
    TASK_CACHE = load_dict_from_json(CACHE_PATH)
except:
    TASK_CACHE = {}
try:
    OBJECT_CACHE = load_dict_from_json(OBJECT_PATH)
except:
    OBJECT_CACHE = {}

# Global configuration
config = {
    "openai": {
        "api_key": os.getenv('OPENAI_API_KEY'),
        "base_url": os.getenv('OPENAI_BASE_URL', "https://api.openai.com/v1"),
        "model": "grok-4",
        "model_detect": "gpt-5-2025-08-07"
    },
    "use_cache": False,
    "detection_service": {
        "host": "localhost",
        "port": 4399
    },
    "prompt_service": {
        "host": "localhost",
        "port": 4599
    },
    "grasper_service": {
        "host": "localhost",
        "port": 4499
    },
    "action_correct_service": {
        "host": "localhost",
        "port": 4699
    },
    "judger_service": {
        "host": "localhost",
        "port": 4799
    }
}

# Initialize OpenAI client
openai_client = None

def init_openai_client():
    """Initialize OpenAI client"""
    global openai_client
    if not config["openai"]["api_key"]:
        raise ValueError("OpenAI API key not set")
    
    openai_client = OpenAI(
        api_key=config["openai"]["api_key"],
        base_url=config["openai"].get("base_url")
    )

def check_services_health():
    """Check health status of services"""
    services_status = {}
    
    # Check detection service
    try:
        detector_url = f"http://{config['detection_service']['host']}:{config['detection_service']['port']}/health"
        response = requests.get(detector_url, timeout=2)
        services_status["detector"] = response.json() if response.status_code == 200 else {"status": "error", "message": response.text}
    except Exception as e:
        services_status["detector"] = {"status": "error", "message": str(e)}
    
    # Check prompt service
    try:
        prompt_url = f"http://{config['prompt_service']['host']}:{config['prompt_service']['port']}/health"
        response = requests.get(prompt_url, timeout=2)
        services_status["prompt_manager"] = response.json() if response.status_code == 200 else {"status": "error", "message": response.text}
    except Exception as e:
        services_status["prompt_manager"] = {"status": "error", "message": str(e)}

    # Check action corrector service
    try:
        corrector_url = f"http://{config['action_correct_service']['host']}:{config['action_correct_service']['port']}/health"
        response = requests.get(corrector_url, timeout=2)
        services_status["action_correct_service"] = response.json() if response.status_code == 200 else {"status": "error", "message": response.text}
    except Exception as e:
        services_status["action_correct_service"] = {"status": "error", "message": str(e)}

    # Check judger service
    try:
        judger_url = f"http://{config['judger_service']['host']}:{config['judger_service']['port']}/health"
        response = requests.get(judger_url, timeout=2)
        services_status["judger_service"] = response.json() if response.status_code == 200 else {"status": "error", "message": response.text}
    except Exception as e:
        services_status["judger_service"] = {"status": "error", "message": str(e)}

    # Check anygrasp service
    try:
        anygrasp_url = f"http://{config['grasper_service']['host']}:{config['grasper_service']['port']}/health"
        response = requests.get(anygrasp_url, timeout=2)
        services_status["match_grasp"] = response.json() if response.status_code == 200 else {"status": "error", "message": response.text}
    except Exception as e:
        services_status["match_grasp"] = {"status": "error", "message": str(e)}
    
    # Check OpenAI client
    services_status["openai"] = {"status": "ok" if openai_client else "error", "message": "Not initialized" if not openai_client else "Ready"}
    
    return services_status

def filter_7d_arrays(input_list, strict_check=True):
    """
    Filter list to keep only 7D arrays (lists of length 7)
    
    Args:
        input_list: Input list containing multiple arrays
        strict_check: Whether to strictly check element types
            True - Ensure each element is numeric
            False - Check length only
    
    Returns:
        Tuple: (Filtered list, List of removed elements)
    """
    valid_arrays = []
    removed_elements = []
    
    for idx, arr in enumerate(input_list):
        try:
            # Check if list/tuple type
            if not isinstance(arr, (list, tuple)):
                raise TypeError(f"Element {idx} is not a list/tuple")
            
            # Check length is 7
            if len(arr) != 7:
                raise ValueError(f"Element {idx} length is not 7")
            
            # Strict mode checks element types
            if strict_check:
                for i, item in enumerate(arr):
                    if not isinstance(item, (int, float)):
                        raise TypeError(f"Element {idx} position {i} is not numeric ({type(item)})")
            
            valid_arrays.append(arr)
            
        except (TypeError, ValueError) as e:
            removed_elements.append({
                'element': arr,
                'index': idx,
                'reason': str(e)
            })
    
    return valid_arrays, removed_elements

def generate_control_sequence(task_desc: str, scene_info: dict, task_type: str = 'default') -> dict:
    """Generate control sequence"""
    global openai_client
    try:
        # Build prompt via prompt service
        prompt_response = requests.post(
            f"http://{config['prompt_service']['host']}:{config['prompt_service']['port']}/build_prompt",
            json={
                "task_description": task_desc,
                "scene_info": scene_info,
                "task_type": task_type
            }
        )
        
        if prompt_response.status_code != 200:
            raise Exception(f"Failed to build prompt: {prompt_response.text}")
        prompt_data = prompt_response.json()
        prompt = prompt_data["prompt"]

        # Use streaming output to avoid issues with certain models
        response = openai_client.chat.completions.create(
            model=config["openai"]["model"],
            messages=prompt["messages"],
            temperature=0.7 if config["openai"]["model"] == "gpt-4o" or config["openai"]["model"] == "gpt-oss-120b" else 1,
            max_tokens=128000 if config["openai"]["model"] == "gpt-5-nano-2025-08-07" else 12800,
            response_format={"type": "json_object"},
            stream=True
        )
        output = ""
        start = time.time()
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                output += chunk.choices[0].delta.content
                print(chunk.choices[0].delta.content, end='', flush=True)
            if time.time() - start > 600:
                raise Exception("OpenAI API timeout")
        print(f'\n[{time.time()-start:.2f}s] Querying OpenAI API...Done')
        control_plan = safe_extract_json_strong(output)

        try:
            control_plan_filtered, _ = filter_7d_arrays(control_plan.get('control_plan').get('sequence'))
        except:
            try:
                control_plan_filtered, _ = filter_7d_arrays(control_plan.get('sequence'))
            except:
                print("Invalid control plan format")
                raise Exception("Invalid control plan format")

        control_plan['sequence'] = control_plan_filtered
        # Add metadata
        result = {
            "control_plan": control_plan,
            "metadata": {
                "task_type": task_type,
                "objects_detected": len(scene_info.get("objects", [])),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return result
    except Exception as e:
        print(f"Error generating sequence: {e}")
        raise

def normalize_task_desc(task_desc: str) -> str:
    """
    Normalize task description, remove brackets and their contents
    """
    return re.sub(r'$$[^$$]*$$', '', task_desc).strip()

def preprocess_sequence_param(s: str) -> str:
    """
    Convert \\" in string to ", while preserving other valid escape characters (like \\n, \\\\ etc.).
    The processed string can be correctly parsed by eval.
    """
    # Use regex to replace \\+ before " with nothing, preserving other escapes
    result = re.sub(r'\\+(?=")', '', s)
    result = result.replace("\\n", "\n")
    return result

def generate_control_sequence_use_cache(task_desc: str, scene_info: dict, task_type: str = 'default') -> dict:
    """Generate control sequence with cache support"""
    global openai_client, TASK_CACHE
    normalized_desc = normalize_task_desc(task_desc)
    if TASK_CACHE.get(normalized_desc, {}) == {}:
        try:
            # Build prompt via prompt service
            prompt_response = requests.post(
                f"http://{config['prompt_service']['host']}:{config['prompt_service']['port']}/build_prompt",
                json={
                    "task_description": task_desc,
                    "scene_info": scene_info,
                    "task_type": task_type
                }
            )
            
            if prompt_response.status_code != 200:
                raise Exception(f"Failed to build prompt: {prompt_response.text}")
            if task_desc.startswith("put") and "on" in task_desc and "[" in task_desc and "]" in task_desc:
                parts = task_desc.split("on")
                object_name = parts[0].replace("put the ", "").strip()
                
                # Extract target position
                position_str = task_desc.split("[")[1].split("]")[0]
                position_parts = position_str.split()
                if len(position_parts) == 3:
                    try:
                        # Handle comma-separated format (e.g., [x, y, z])
                        if any(',' in part for part in position_parts):
                            position_parts = [p.replace(',', '') for p in position_str.split(',')]
                        
                        target_x = float(position_parts[0])
                        target_y = float(position_parts[1])
                        target_z = float(position_parts[2])
                    except ValueError:
                        return {
                            "answer": False,
                            "reason": "Invalid position format",
                            "task_type": "invalid_format"
                        }
                if len(position_parts) == 6:
                    try:
                        # Handle comma-separated format (e.g., [x, y, z])
                        if any(',' in part for part in position_parts):
                            position_parts = [p.replace(',', '') for p in position_str.split(',')]
                        
                        target_x = float(position_parts[0])
                        target_y = float(position_parts[1])
                        target_z = float(position_parts[2])
                        target_roll = float(position_parts[3])
                        target_pitch = float(position_parts[4])
                        target_yaw = float(position_parts[5])
                    except ValueError:
                        return {
                            "answer": False,
                            "reason": "Invalid position format",
                            "task_type": "invalid_format"
                        }

            prompt_data = prompt_response.json()
            prompt = prompt_data["prompt"]
            time_control_ask_start = time.time()

            # Use streaming output to avoid issues with certain models
            response = openai_client.chat.completions.create(
                model=config["openai"]["model"],
                messages=prompt["messages"],
                temperature=0.7,
                max_tokens=12000,
                response_format={"type": "json_object"},
                stream=True
            )
            output = ""
            start = time.time()
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    output += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end='', flush=True)
            print(f'[{time.time()-start:.2f}s] Querying OpenAI API...Done')
            control_plan = safe_extract_json_strong(output)
            if control_plan.get('sequence') == None:
                control_plan_filtered, _ = filter_7d_arrays(control_plan.get('control_plan').get('sequence'))
                safe_sequence_param = preprocess_sequence_param(control_plan.get('control_plan').get('sequence_param'))
                TASK_CACHE[normalized_desc] = safe_sequence_param
                save_dict_to_json(TASK_CACHE, CACHE_PATH)
            else:
                control_plan_filtered, _ = filter_7d_arrays(control_plan.get('sequence'))
                if control_plan.get('sequence_param') != 'sequence_param':
                    safe_sequence_param = preprocess_sequence_param(control_plan.get('sequence_param'))
                    TASK_CACHE[normalized_desc] = safe_sequence_param
                    save_dict_to_json(TASK_CACHE, CACHE_PATH)
                else:
                    try:
                        safe_sequence_param = preprocess_sequence_param(control_plan.get('sequence_param').get('sequence_param'))
                        TASK_CACHE[normalized_desc] = safe_sequence_param
                        save_dict_to_json(TASK_CACHE, CACHE_PATH)
                    except:
                        raise ValueError("sequence_param in control_plan does not exist")

            control_plan['sequence'] = control_plan_filtered
            # Add metadata
            result = {
                "control_plan": control_plan,
                "metadata": {
                    "task_type": task_type,
                    "objects_detected": len(scene_info.get("objects", [])),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            return result
        except Exception as e:
            print(f"Error generating sequence: {e}")
            raise
    elif TASK_CACHE.get(normalized_desc, {}) != {}:
        # Use cache
        cache_action_list = TASK_CACHE.get(normalized_desc)
        if (task_desc.startswith("put") or task_desc.startswith(" put")) and "on" in task_desc and "[" in task_desc and "]" in task_desc:
            parts = task_desc.split("on")
            object_name = parts[0].replace("put the ", "").strip()
            
            # Extract target position
            position_str = task_desc.split("[")[1].split("]")[0]
            position_parts = position_str.split()
            if len(position_parts) == 3:
                try:
                    # Handle comma-separated format (e.g., [x, y, z])
                    if any(',' in part for part in position_parts):
                        position_parts = [p.replace(',', '') for p in position_str.split(',')]
                    
                    target_x = float(position_parts[0])
                    target_y = float(position_parts[1])
                    target_z = float(position_parts[2])
                except ValueError:
                    return {
                        "answer": False,
                        "reason": "Invalid position format",
                        "task_type": "invalid_format"
                    }
            if len(position_parts) == 6:
                try:
                    # Handle comma-separated format (e.g., [x, y, z])
                    if any(',' in part for part in position_parts):
                        position_parts = [p.replace(',', '') for p in position_str.split(',')]
                    
                    target_x = float(position_parts[0])
                    target_y = float(position_parts[1])
                    target_z = float(position_parts[2])
                    target_roll = float(position_parts[3])
                    target_pitch = float(position_parts[4])
                    target_yaw = float(position_parts[5])
                except ValueError:
                    return {
                        "answer": False,
                        "reason": "Invalid position format",
                        "task_type": "invalid_format"
                    }
        if isinstance(cache_action_list, str):
            try:
                action_list = eval(cache_action_list)
            except:
                print("Parameterized action sequence is invalid")
        if isinstance(cache_action_list, list):
            try:
                action_list = eval(cache_action_list)
            except:
                print("Parameterized action sequence is invalid")
        control_plan = {}
        control_plan['sequence'] = action_list

        # Add metadata
        result = {
            "control_plan": control_plan,
            "metadata": {
                "task_type": task_type,
                "objects_detected": len(scene_info.get("objects", [])),
                "timestamp": datetime.now().isoformat()
            }
        }
        return result

def save_task_log(task_desc: str, scene_info: dict, control_result: dict, execution_result: dict = None, execution_list: dict = None):
    """Save task log"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(LOG_DIR, timestamp)
    os.makedirs(log_dir, exist_ok=True)
    
    # Save control plan
    plan_path = os.path.join(log_dir, "control_plan.json")
    with open(plan_path, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "task_description": task_desc,
            "scene_info": scene_info,
            "control_result": control_result,
            "execution_result": execution_result,
            "execution_list": execution_list
        }, f, indent=2)
    
    print(f"Task log saved to: {log_dir}")
    return log_dir

def safe_extract_json_strong(content: str) -> dict:
    """
    Enhanced JSON parsing:
    1. Try direct parsing of pure JSON
    2. If fails, try cleaning Markdown code blocks then parse
    3. If still fails, try removing comments (// or /* */) then parse
    4. Final failure returns raw content
    """
    # Case 1: Direct parse pure JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Case 2: Handle Markdown code block wrapped JSON
    markdown_pattern = r'```(?:json)?\n(.*?)\n```'
    markdown_match = re.search(markdown_pattern, content, re.DOTALL)
    if markdown_match:
        try:
            return json.loads(markdown_match.group(1).strip())
        except json.JSONDecodeError:
            pass  # Continue to other cleanup

    # Case 3: Handle non-standard JSON with comments
    try:
        # Remove single-line (//) and multi-line (/* */) comments
        cleaned_content = re.sub(
            r'//.*?$|/\*.*?\*/', '', 
            content, flags=re.DOTALL | re.MULTILINE
        )
        # Remove trailing commas (e.g., "}," -> "}")
        cleaned_content = re.sub(r',\s*([}$$])', r'\1', cleaned_content)
        return json.loads(cleaned_content)
    except json.JSONDecodeError:
        pass

    try:
        json_pattern = re.compile(r'\s*\{\s*"sequence":.*?"steps_description":.*?\}\s*', re.DOTALL)
        match = json_pattern.search(content)
        if match:
            # Extract matched JSON string
            json_str = match.group()
            # Parse JSON to dict
            return json.loads(json_str)

    except json.JSONDecodeError:
        pass

    # Case 4: Unable to parse, return raw content
    return {"raw_content": content}

@app.route('/process_frame', methods=['POST'])
def process_task():
    try:
        # Get task description
        start_time = time.time()
        task_desc = request.form.get('text')
        if not task_desc:
            return jsonify({"error": "Missing task description"}), 400
        recording_state = request.form.get("recording_state")
        task_type = request.form.get('task_type', 'default')
        use_cache = request.form.get('use_cache', str(config.get("use_cache", False)).lower()) == 'true'

        # Create temp directory for files
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_tasks', task_id)
        os.makedirs(task_dir, exist_ok=True)
        print(f"File acquisition took {time.time()-start_time}s")

        # Process image data
        scene_data = {}
        cameras_data = {}
        
        # Process RGB images
        if 'image' in request.files:
            for rgb_file in request.files.getlist('image'):
                # Extract camera name (e.g., from "front.png" extract "front")
                camera_name = os.path.splitext(rgb_file.filename)[0]
                
                # Save RGB image
                rgb_data = Image.open(rgb_file)
                rgb_buffer = io.BytesIO()
                save_time_start = time.time()
                rgb_data.save(rgb_buffer, format='JPEG', quality=100)
                rgb_buffer.seek(0)
                print(f"rgb_data.save(rgb_buffer, format='JPEG', quality=100) took {time.time()-save_time_start}s")
                
                # Store camera data
                cameras_data[camera_name] = {
                    'rgb_data': rgb_data,
                    'rgb_buffer': rgb_buffer
                }
        else:
            return jsonify({"error": "Missing RGB image"}), 400
        print(f"RGB file saving took {time.time()-start_time}s")

        # Process depth images
        if 'depth' in request.files:
            for depth_file in request.files.getlist('depth'):
                # Extract camera name (e.g., from "front_depth.pkl" extract "front")
                filename = os.path.splitext(depth_file.filename)[0]
                camera_name = filename.replace('_depth', '')
                # Load depth data
                depth_data = pickle.loads(depth_file.read())
                # Save depth image
                depth_path = os.path.join(task_dir, f"{filename}.pkl")
                with open(depth_path, 'wb') as f:
                    pickle.dump(depth_data, f)
                
                # Store camera data
                if camera_name in cameras_data:
                    cameras_data[camera_name]['depth_path'] = depth_path
                    cameras_data[camera_name]['depth_data'] = depth_data
                else:
                    cameras_data[camera_name] = {
                        'depth_path': depth_path,
                        'depth_data': depth_data
                    }
        print(f"Depth file saving took {time.time()-start_time}s")

        scene_data['cameras'] = cameras_data
        # Get camera parameters
        camera_params = request.form.get('camera_params')
        if camera_params:
            scene_data['camera_params'] = json.loads(camera_params)
        print(f"Initialization took {time.time()-start_time}s")
            

        # Step 1: Query GPT for objects to detect
        prompt_for_detection = {
            "task_description": task_desc,
            "scene_info": {},
            "task_type": "detection_request"
        }
        
        detection_prompt_response = requests.post(
            f"http://{config['prompt_service']['host']}:{config['prompt_service']['port']}/build_prompt",
            json=prompt_for_detection
        )
        
        if detection_prompt_response.status_code != 200:
            raise Exception(f"Failed to build detection prompt: {detection_prompt_response.text}")
        
        detection_prompt_data = detection_prompt_response.json()
        detection_prompt = detection_prompt_data["prompt"]["messages"]
        
        time_detect_ask_start = time.time()
        normalized_desc = normalize_task_desc(task_desc)
        if OBJECT_CACHE.get(normalized_desc, []) == []:

            # Use streaming output to avoid issues with certain models
            response = openai_client.chat.completions.create(
                model=config["openai"]["model_detect"],
                messages=detection_prompt,
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"},
                stream=True
            )
            output = ""
            start = time.time()
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    output += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end='', flush=True)
            print(f'\n[{time.time()-start:.2f}s] Querying OpenAI API...Done')
            content = safe_extract_json_strong(output)
            # Parse objects to detect
            objects_to_detect = content.get("object_to_detect", [])
            if use_cache:
                OBJECT_CACHE[normalized_desc] = objects_to_detect
                save_dict_to_json(OBJECT_CACHE, OBJECT_PATH)
        else:
            objects_to_detect = OBJECT_CACHE.get(normalized_desc)

        
        detect_time_start = time.time()

        # Step 2: Call detection service for 3D detection sequentially
        scene_info = {"objects": []}
        detection_url = f"http://{config['detection_service']['host']}:{config['detection_service']['port']}/detect_3d"
        anygrasp_url = f"http://{config['grasper_service']['host']}:{config['grasper_service']['port']}/match_grasp"
        corrector_url = f"http://{config['action_correct_service']['host']}:{config['action_correct_service']['port']}/correct_actions"
        judger_url = f"http://{config['judger_service']['host']}:{config['judger_service']['port']}/judger"
        services_status = check_services_health()
        if services_status.get("match_grasp").get("status") != 'error':
            use_anygrasp = True
        else:
            print(f'Current time: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}, anygrasp service unavailable, waiting for service restart!!')
            input("Press any key to continue")
            while services_status.get("match_grasp").get("status") == 'error':
                services_status = check_services_health()
                input("Press any key to continue")
            use_anygrasp = True
        i = 0
        for obj_name in objects_to_detect:
            front_intrinsics = scene_data['camera_params'].get('intrinsics', [[]])[0]  # 0 is front, 1 is side
            front_extrinsics = scene_data['camera_params'].get('extrinsics', [[]])[0] 

            detection_data = {
                'text': obj_name,
                'task_prompt': task_desc,
                'camera_params': json.dumps({
                    'intrinsics': front_intrinsics,
                    'extrinsics': front_extrinsics
                })
            }
            open_start = time.time()
            with open(cameras_data['front']['depth_path'], 'rb') as depth_f:
                rgb_buffer = cameras_data['front']['rgb_buffer']
                rgb_buffer.seek(0)
                detection_files = {
                    'rgb_image': ('rgb.png', rgb_buffer, 'image/png'),
                    'depth_image': ('depth.pkl', depth_f)
                }
                detect3d_time_start = time.time()
                print(f"File opening took {detect3d_time_start-open_start}s")
                detection_result = requests.post(
                    detection_url,
                    files=detection_files,
                    data=detection_data
                )
                print(f"Detection took {time.time()-detect3d_time_start}s")
                if detection_result.status_code == 200:
                    scene_info["objects"].extend(detection_result.json().get("results", []))

                else:
                    raise Exception(f"Detection failed for {obj_name}: {detection_result.text}")
                scene_info["objects"][i]['position_3d_baselink']['orientation_rpy'] = [0.1, 1.56, 0.0]
                scene_info["objects"][i]['position_3d_baselink']['grasp_x'] = scene_info["objects"][i]['position_3d_baselink']['x']
                scene_info["objects"][i]['position_3d_baselink']['grasp_y'] = scene_info["objects"][i]['position_3d_baselink']['y']
                scene_info["objects"][i]['position_3d_baselink']['grasp_z'] = scene_info["objects"][i]['position_3d_baselink']['z']
                i = i + 1
        print(f"Detection total took {time.time()-detect_time_start}s")
        # Step 0: Confirm task is not completed
        judge_time_start = time.time()
        services_status = check_services_health()
        if services_status.get("judger_service").get("status") != 'error':
            use_judger = True
        else:
            use_judger = False
        if use_judger:
            judger_data = {
                'text': task_desc,
                'scene_info': json.dumps(scene_info),
                'camera_params': json.dumps({
                    'intrinsics': front_intrinsics,
                    'extrinsics': front_extrinsics
                })
            }
            with open(cameras_data['front']['depth_path'], 'rb') as depth_f:
                rgb_buffer = cameras_data['front']['rgb_buffer']
                rgb_buffer.seek(0)
                detection_files = {
                    'rgb_image': ('rgb.png', rgb_buffer, 'image/png'),
                    'depth_image': ('depth.pkl', depth_f)
                }
            
                judger_response = requests.post(
                    judger_url,
                    files=detection_files,
                    data=judger_data
                )
                judger_response = judger_response.json()
            if judger_response['response']['answer'] == True:
                response = {
                    "status": "success",
                    'response': "False",
                    'scene_info': json.dumps(scene_info)
                }
                print("Work has been done!!!")
                return jsonify(response)
            if recording_state == RECORDING_STATES["RECORDING"]:
                response = {
                    "status": "success",
                    'response': "True",
                    'scene_info': json.dumps(scene_info)
                }
                print("Task failed, return abort recording signal")
                return jsonify(response)
        print(f"Judging took {time.time()-judge_time_start}s")
        
        i = 0
        if use_anygrasp:
            for detection_result in scene_info["objects"]:
                anygrasp_time_start = time.time()
                target_position = [detection_result['position_3d_baselink']['x'],
                                    detection_result['position_3d_baselink']['y'],
                                    detection_result['position_3d_baselink']['z']]
                data_grasp = {'target_position': json.dumps(target_position),
                                'camera_params': json.dumps(scene_data.get('camera_params', {})),
                                'factor_depth': json.dumps(1000.0)  # Depth factor
                                }
                
                # Initialize file data
                detection_files = {}
                # Process all camera data
                for camera_name, camera_data in scene_data['cameras'].items():
                    # Get current camera's RGB and depth data
                    rgb_data = camera_data['rgb_data']
                    depth_data = camera_data['depth_data']
                    
                    # Convert PIL Image to BytesIO for direct sending
                    rgb_buffer = io.BytesIO()
                    save_time_start = time.time()
                    rgb_data.save(rgb_buffer, format='JPEG', quality=100)
                    rgb_buffer.seek(0)
                    print(f"rgb_data.save(rgb_buffer, format=\"JPEG\", quality=100) took {time.time()-save_time_start}s")
                    rgb_buffer.seek(0)
                    
                    # Serialize depth data
                    depth_buffer = io.BytesIO()
                    pickle.dump(depth_data, depth_buffer)
                    depth_buffer.seek(0)
                    
                    # Add to file data, use camera name as distinguisher
                    detection_files[f'rgb_image_{camera_name}'] = (f'rgb_{camera_name}.png', rgb_buffer)
                    detection_files[f'depth_image_{camera_name}'] = (f'depth_{camera_name}.pkl', depth_buffer)
                
                # Send request with all camera data
                match_grasp = requests.post(
                    anygrasp_url,
                    files=detection_files,
                    data=data_grasp
                )
                try:
                    scene_info["objects"][i]['position_3d_baselink']['orientation_rpy'] = match_grasp.json().get('orientation').get('rpy')
                    rpy = scene_info["objects"][i]['position_3d_baselink']['orientation_rpy']
                    scene_info["objects"][i]['position_3d_baselink']['grasp_x'] = match_grasp.json().get('position')[0]
                    scene_info["objects"][i]['position_3d_baselink']['grasp_y'] = match_grasp.json().get('position')[1]
                    scene_info["objects"][i]['position_3d_baselink']['grasp_z'] = match_grasp.json().get('position')[2]
                    print(f"Anygrasp output pose: {rpy}")
                    print(f"Anygrasp took {time.time()-anygrasp_time_start}s")
                except:
                    raise ValueError("No grasp obtained")
                i = i + 1

        # Step 3: Generate control sequence
        if use_cache:
            control_result = generate_control_sequence_use_cache(task_desc, scene_info, task_type)
        else:
            control_result = generate_control_sequence(task_desc, scene_info, task_type)
        
        # Execute control sequence
        execution_result = None
        try:
            execute_list = control_result.get('control_plan', {}).get('control_plan', {}).get('sequence', [])
        except:
            try:
                execute_list = control_result.get('control_plan', {}).get('sequence', [])
            except:
                raise ValueError("Invalid control_result format")

        if execute_list == [] or execute_list == {}:
            execute_list = control_result.get('control_plan', {}).get('sequence', [])
        
        services_status = check_services_health()
        if services_status.get("action_correct_service").get("status") != 'error':
            use_corrector = True
        else:
            use_corrector = False
        if use_corrector:
            correct_result = requests.post(
                        corrector_url,
                        json={'response': execute_list}
                        )
            if correct_result.status_code == 200:
                correct_result = correct_result.json()
            execute_list = correct_result['corrected_actions']

        # Save task log
        log_dir = save_task_log(task_desc, scene_info, control_result, execution_result, execute_list)
        
        # Prepare response
        response = {
            "status": "success",
            "task_description": task_desc,
            "control_plan": control_result.get('control_plan', {}),
            "metadata": {
                **control_result.get('metadata', {}),
                "log_dir": log_dir,
                "object_count": len(scene_info.get('objects', [])) 
            },
            'response': execute_list,
            'scene_info': json.dumps(scene_info)
        }
        print('execute_list:', execute_list)
        print(f"Total time: {time.time()-start_time}s")
        return jsonify(response)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing task: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(check_services_health())

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, help="Model name for action generation")
    parser.add_argument("--model-detect", type=str, help="Model name for object detection query")
    parser.add_argument("--use-cache", action="store_true", help="Enable parameterized action sequence caching")
    parser.add_argument("--port", type=int, default=9500, help="Port to run the controller service on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    args = parser.parse_args()
    
    # Update configuration
    if args.model:
        config["openai"]["model"] = args.model
    if args.model_detect:
        config["openai"]["model_detect"] = args.model_detect
    if args.use_cache is not None:
        config["use_cache"] = args.use_cache
    
    # Initialize OpenAI client
    try:
        init_openai_client()
        print("OpenAI client initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize OpenAI client: {e}")
    
    # Check services health
    print("Checking services health...")
    services_health = check_services_health()
    for service, status in services_health.items():
        print(f"  - {service}: {status['status']}")
    
    # Start service
    print(f"Starting controller service on {args.host}:{args.port}...")
    app.run(host=args.host, port=args.port, debug=False)
