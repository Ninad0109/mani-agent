# detector/app.py
from flask import Flask, request, jsonify
import torch
from PIL import Image, ImageDraw, ImageFont
import io
import json
import pickle
import numpy as np
import os
import sys
from datetime import datetime
import time
from transformers import AutoProcessor, AutoModelForCausalLM

# Add project root directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.transforms import pixel_to_3d_baselink

import cv2

from openai import OpenAI
import base64
import re

app = Flask(__name__)

# Create log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configuration
config = {
    "box_threshold": 0.35,
    "cpu_only": False
}

# Global variables
model = None
processor = None
client = None
vlm_model = "gpt-5-2025-08-07"

def load_model(model_name="microsoft/Florence-2-large", cpu_only=False):
    """Load Florence2 model"""
    device = "cuda:0" if not cpu_only and torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() and not cpu_only else torch.float32
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        torch_dtype=torch_dtype, 
        trust_remote_code=True
    ).to(device)
    
    processor = AutoProcessor.from_pretrained(
        model_name, 
        trust_remote_code=True
    )
    
    return model, processor

def load_image_from_bytes(rgb_file):
    """Load image from bytes data"""
    try:
        image_pil = Image.open(rgb_file).convert("RGB")
    except:
        image_pil = Image.open(io.BytesIO(rgb_file.read())).convert("RGB")
    return image_pil

def load_image_from_bytes_fix(rgb_file):
    """Load image from bytes data with fix"""
    start_time = time.time()
    try:
        image_pil = Image.open(rgb_file).convert("RGB")
    except:
        # Try converting byte stream to BytesIO then read
        rgb_bytes = rgb_file.read()  # Read all bytes first
        if not rgb_bytes:
            raise ValueError("Image byte stream is empty")
        image_pil = Image.open(io.BytesIO(rgb_bytes)).convert("RGB")
        print(f"Image loading took {time.time()-start_time}s")
    return image_pil

def get_florence_detection(model, processor, image, text_prompt, box_threshold=0.35):
    """Perform Florence2 detection"""
    device = "cuda:0" if not config["cpu_only"] and torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() and not config["cpu_only"] else torch.float32
    
    # Use open vocabulary detection
    if text_prompt.strip():
        prompt = "<OPEN_VOCABULARY_DETECTION>"
        full_prompt = prompt + "every " + text_prompt.strip()
    else:
        # If no text specified, use standard object detection
        prompt = "<OD>"
        full_prompt = prompt
    
    inference_time = time.time()
    inputs = processor(text=full_prompt, images=image, return_tensors="pt").to(device, torch_dtype)
    
    with torch.no_grad():
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            num_beams=3,
            do_sample=False
        )
    
    print(f"Inference time: {time.time()-inference_time}s")
    
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed_answer = processor.post_process_generation(
        generated_text, 
        task=prompt, 
        image_size=(image.width, image.height)
    )
    
    return parsed_answer

def convert_florence_to_standard_format(florence_results, image_width, image_height, box_threshold=0.35):
    """
    Convert Florence2 detection results to standard format
    Return normalized (x_center, y_center, x, y, w, h) and related info
    """
    results = []
    
    # Handle open vocabulary detection results
    if '<OPEN_VOCABULARY_DETECTION>' in florence_results:
        bboxes = florence_results['<OPEN_VOCABULARY_DETECTION>']['bboxes']
        labels = florence_results['<OPEN_VOCABULARY_DETECTION>']['bboxes_labels']
        
        for bbox, label in zip(bboxes, labels):
            x1, y1, x2, y2 = bbox
            
            # Convert to normalized coordinates
            x1_norm = x1 / image_width
            y1_norm = y1 / image_height
            x2_norm = x2 / image_width
            y2_norm = y2 / image_height
            
            # Compute center and width/height
            x_center = (x1_norm + x2_norm) / 2
            y_center = (y1_norm + y2_norm) / 2
            width = x2_norm - x1_norm
            height = y2_norm - y1_norm
            
            # Format: (x_center, y_center, x, y, w, h)
            detection = [x_center, y_center, x1_norm, y1_norm, width, height]
            
            results.append({
                'detection': detection,
                'label': label,
                'confidence': 0.8  # Florence2 does not provide confidence directly, use default
            })
    
    # Handle standard object detection results
    elif '<OD>' in florence_results:
        bboxes = florence_results['<OD>']['bboxes']
        labels = florence_results['<OD>']['labels']
        scores = florence_results['<OD>'].get('scores', [0.8] * len(labels))
        
        for bbox, label, score in zip(bboxes, labels, scores):
            if score < box_threshold:
                continue
                
            x1, y1, x2, y2 = bbox
            
            # Convert to normalized coordinates
            x1_norm = x1 / image_width
            y1_norm = y1 / image_height
            x2_norm = x2 / image_width
            y2_norm = y2 / image_height
            
            # Compute center and width/height
            x_center = (x1_norm + x2_norm) / 2
            y_center = (y1_norm + y2_norm) / 2
            width = x2_norm - x1_norm
            height = y2_norm - y1_norm
            
            # Format: (x_center, y_center, x, y, w, h)
            detection = [x_center, y_center, x1_norm, y1_norm, width, height]
            
            results.append({
                'detection': detection,
                'label': label,
                'confidence': score
            })
    
    return results

def draw_dashed_rectangle(draw, bbox, color, width=2, dash_length=5):
    """Draw dashed rectangle for older Pillow versions"""
    x1, y1, x2, y2 = bbox
    
    # Draw top edge
    for i in range(0, int(x2-x1), dash_length*2):
        draw.line([x1+i, y1, min(x1+i+dash_length, x2), y1], 
                 fill=color, width=width)
    
    # Draw bottom edge
    for i in range(0, int(x2-x1), dash_length*2):
        draw.line([x1+i, y2, min(x1+i+dash_length, x2), y2], 
                 fill=color, width=width)
    
    # Draw left edge
    for i in range(0, int(y2-y1), dash_length*2):
        draw.line([x1, y1+i, x1, min(y1+i+dash_length, y2)], 
                 fill=color, width=width)
    
    # Draw right edge
    for i in range(0, int(y2-y1), dash_length*2):
        draw.line([x2, y1+i, x2, min(y1+i+dash_length, y2)], 
                 fill=color, width=width)

def save_detection_log(image_data, image_anno, text_prompt, results, florence_results=None):
    """Save detection log and visualization image"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S.%f")
    log_dir = os.path.join(LOG_DIR, timestamp)
    os.makedirs(log_dir, exist_ok=True)
    
    # Save original image
    image_path = os.path.join(log_dir, "input_image.jpg")
    if isinstance(image_data, bytes):
        with open(image_path, "wb") as f:
            f.write(image_data)
        image_pil = Image.open(io.BytesIO(image_data))
    else:
        image_data.save(image_path)
        image_pil = image_data
    
    # Create visualization image
    if florence_results:
        vis_image = image_pil.copy()
        draw = ImageDraw.Draw(vis_image)
        
        # Try to load font
        try:
            font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 18)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            except:
                font = ImageFont.load_default()
        
        # Draw detection results
        if '<OPEN_VOCABULARY_DETECTION>' in florence_results:
            bboxes = florence_results['<OPEN_VOCABULARY_DETECTION>']['bboxes']
            labels = florence_results['<OPEN_VOCABULARY_DETECTION>']['bboxes_labels']
            
            for bbox, label in zip(bboxes, labels):
                x1, y1, x2, y2 = map(int, bbox)
                # Draw red dashed box
                draw_dashed_rectangle(draw, [x1, y1, x2, y2], "red", width=2, dash_length=5)
                # Draw label
                text = f"{label} (ovd)"
                text_bbox = draw.textbbox((x1, max(0, y1-25)), text, font=font)
                draw.rectangle([text_bbox[0]-2, text_bbox[1]-2, text_bbox[2]+2, text_bbox[3]+2], fill="red")
                draw.text((x1, max(0, y1-25)), text, fill="white", font=font)
        
        elif '<OD>' in florence_results:
            bboxes = florence_results['<OD>']['bboxes']
            labels = florence_results['<OD>']['labels']
            scores = florence_results['<OD>'].get('scores', [0.8] * len(labels))
            
            for bbox, label, score in zip(bboxes, labels, scores):
                x1, y1, x2, y2 = map(int, bbox)
                # Draw blue solid box
                draw.rectangle([x1, y1, x2, y2], outline="blue", width=2)
                # Draw label and confidence
                text = f"{label} ({score:.2f})"
                text_bbox = draw.textbbox((x1, y1), text, font=font)
                draw.rectangle([text_bbox[0]-2, text_bbox[1]-2, text_bbox[2]+2, text_bbox[3]+2], fill="blue")
                draw.text((x1, y1), text, fill="white", font=font)
        
        # Save visualization image
        vis_path = os.path.join(log_dir, "detection_visualization.jpg")
        vis_image.save(vis_path)
        if image_anno is not None:
            vis_path_anno = os.path.join(log_dir, "detection_visualization_gpt_hint.jpg")
            image_anno.save(vis_path_anno, format="JPEG", quality=100)

        print(f"Visualization saved to: {vis_path}")
    
    # Save detection results
    results_path = os.path.join(log_dir, "detection_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "prompt": text_prompt,
            "results": results,
            "florence_raw_results": florence_results
        }, f, indent=2)
    
    print(f"Detection log saved to: {log_dir}")

def safe_extract_json_strong(content: str) -> dict:
    """
    Enhanced JSON parsing:
    1. Try direct parsing of pure JSON first
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
            pass  # Continue to other cleanup methods

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

@app.route('/detect', methods=['POST'])
def detect_objects():
    global model, processor, config
    
    if 'image' not in request.files or 'text' not in request.form:
        return jsonify({"error": "Missing image or text parameter"}), 400
    
    try:
        # Get input
        image_file = request.files['image']
        text_prompt = request.form['text']
        box_threshold = float(request.form.get('box_threshold', config["box_threshold"]))
        
        # Process image
        image_pil = load_image_from_bytes(image_file)
        W, H = image_pil.size
        
        # Run Florence2 detection
        florence_results = get_florence_detection(
            model, 
            processor,
            image_pil, 
            text_prompt
        )
        
        # Convert to standard format
        converted_results = convert_florence_to_standard_format(
            florence_results, W, H, box_threshold
        )
        
        # Prepare output
        results = []
        for item in converted_results:
            x_center, y_center, x, y, w, h = item['detection']
            results.append({
                "object_name": item['label'],
                "confidence": item['confidence'],
                "center_position": {"x": x_center, "y": y_center},
                "bounding_box": {
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h
                }
            })
        
        # Save log
        save_detection_log(image_pil, None, text_prompt, results, florence_results)
        
        return jsonify({"results": results})
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in detection: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/detect_3d', methods=['POST'])
def detect_objects_3d():
    global model, processor, config, vlm_model
    
    if 'rgb_image' not in request.files or 'depth_image' not in request.files:
        return jsonify({"error": "Missing rgb_image or depth_image"}), 400
    
    if 'text' not in request.form or 'camera_params' not in request.form:
        return jsonify({"error": "Missing text or camera_params"}), 400
    
    try:
        # Get input
        rgb_file = request.files['rgb_image']
        depth_file = request.files['depth_image']
        text_prompt = request.form['text']
        camera_params = json.loads(request.form['camera_params'])
        box_threshold = float(request.form.get('box_threshold', config["box_threshold"]))
        task_prompt = request.form.get('task_prompt', "")
        
        # Process RGB image for detection
        try:
            image_pil = load_image_from_bytes(rgb_file)
        except:
            image_pil = load_image_from_bytes_fix(rgb_file)
        W, H = image_pil.size
        
        # Read depth image
        depth_bytes = depth_file.read()
        depth_image = pickle.loads(depth_bytes)
        
        # Run Florence2 detection
        det_time_start = time.time()
        florence_results = get_florence_detection(
            model, 
            processor,
            image_pil, 
            text_prompt
        )
        print(f"Detection took {time.time()-det_time_start}s")
        
        # Convert to standard format
        converted_results = convert_florence_to_standard_format(
            florence_results, W, H, box_threshold
        )
        image_pil_anno = None
        if len(converted_results) > 1 and (task_prompt != ""):
            print("Multiple instances of the same object detected. Selecting the appropriate one based on task description!")
            image = np.array(image_pil)
            # Convert to BGR for OpenCV
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            for i, item in enumerate(converted_results):
                x_center, y_center, x, y, w, h = item['detection']
                # Convert normalized to pixel coordinates
                x_pixel = int(x_center * W)
                y_pixel = int(y_center * H)
                cv2.circle(image, (x_pixel, y_pixel), 10, (0, 255, 0), -1)  # Green circle
                cv2.putText(image, str(i), (x_pixel+5, y_pixel+5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)  # Red number
            # Convert back to RGB
            annotated_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_pil_anno = Image.fromarray(annotated_image)

            buffer = io.BytesIO()
            image_pil_anno.save(buffer, format="JPEG", quality=100)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{image_base64}"
            prompt = f"""Please carefully look at the picture and help me determine the correct object for my task based on the following information:

            - Task requirement: {task_prompt}
            - Target object name: {text_prompt}
            - Reference image: The image contains multiple instances of "{text_prompt}", each labeled with a number (0, 1, 2, 3, etc.)

            Your task is to identify which numbered instance of "{text_prompt}" is the most suitable for completing the task.

            Notice that the index begin with 0!

            Please judge directly according to the relative position in the picture.

            Return your answer ONLY in the following JSON format with no extra characters, quotes, or explanations:
            {{
            "selected_labels": [0]
            }}"""

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_uri  # Ensure this is full "data:image/jpeg;base64,..." format
                            }
                        }
                    ]
                }
            ]
            # Call OpenAI API
            response = client.chat.completions.create(
                model=vlm_model, # qwen2.5-vl-72b-instruct o4-mini claude-sonnet-4-20250514 ,qwen3-235b-a22b
                messages=messages,
                max_tokens=9000, # 4096 for qwen2.5-vl-72b-instruct
                response_format={"type": "json_object"}
            )
            output = response.choices[0].message.content

            response_text = output
            index = safe_extract_json_strong(response_text)
            index_keep = index.get("selected_labels", [0])
            print(f"selected_labels: {index_keep}")
            converted_results = [converted_results[i] for i in index_keep if 0 <= i < len(converted_results)]
            
        # Prepare output results
        results = []
        for item in converted_results:
            x_center, y_center, x, y, w, h = item['detection']
            
            # Convert normalized to pixel coordinates
            x_pixel = int(x_center * W)
            y_pixel = int(y_center * H)
            
            # Get depth value (depth image in mm, convert to m)
            depth_value = depth_image[y_pixel, x_pixel] / 1000.0
            while depth_value == 0 and y_pixel < depth_image.shape[0] - 1:
                y_pixel += 1
                print("Depth value is 0, searching for another pixel")
                depth_value = depth_image[y_pixel, x_pixel] / 1000.0
            
            # Compute 3D position
            position_3d = pixel_to_3d_baselink(
                x_pixel, y_pixel, depth_value,
                camera_params['intrinsics'],
                camera_params['extrinsics']
            )
            
            results.append({
                "object_name": text_prompt,
                "confidence": item['confidence'],
                "position_3d_baselink": {
                    "x": position_3d[0],
                    "y": position_3d[1],
                    "z": position_3d[2]-0.01
                }
            })
        
        # Save log
        try:
            save_detection_log(image_pil, image_pil_anno, text_prompt, results, florence_results)
        except:
            save_detection_log(image_pil, None, text_prompt, results, florence_results)
        
        return jsonify({"results": results})
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in 3D detection: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    if model is None or processor is None:
        return jsonify({"status": "error", "message": "Model not loaded"}), 503
    return jsonify({"status": "ok", "device": "cuda" if torch.cuda.is_available() else "cpu"})

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--detect-model", type=str, default="microsoft/Florence-2-large", help="Model name for detection")
    parser.add_argument("--vlm-model", type=str, default="gpt-5-2025-08-07", help="Model name for VLM object selection")
    parser.add_argument("--port", type=int, default=4399, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    args = parser.parse_args()
    
    # Update globals
    vlm_model = args.vlm_model
    
    # Initialize OpenAI client
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    # Load model
    print("Loading detection model...")
    model, processor = load_model(model_name=args.detect_model, cpu_only=config["cpu_only"])
    device = "cuda:0" if not config["cpu_only"] and torch.cuda.is_available() else "cpu"
    print(f"Detection model loaded. Using device: {device}")
    
    # Start service
    app.run(host=args.host, port=args.port, debug=False)
