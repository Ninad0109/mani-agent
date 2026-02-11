# 🔍 Monitoring Integration Guide

This guide shows how to integrate execution tracing, cost tracking, and GPU monitoring into ManiAgent.

## 📦 Installation

First, install the required monitoring dependencies:

```bash
pip install gputil psutil flask
```

Add to `requirements.txt`:
```
gputil>=1.4.0
psutil>=5.9.0
```

## 🚀 Quick Start

### 1. Start the Monitoring Dashboard

```bash
python monitoring_dashboard.py
```

Then open http://localhost:5000 in your browser to see:
- 📊 Real-time GPU/CPU usage
- 💰 API cost tracking
- 🔍 Execution traces
- 📈 Historical metrics

### 2. Integrate into Controller

Add these imports at the top of `controller/app.py`:

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.monitoring import tracer, cost_tracker, gpu_monitor

# Start GPU monitoring when app starts
gpu_monitor.start_monitoring(interval=2.0)
```

### 3. Add Tracing to Endpoints

Wrap your main endpoint with tracing:

```python
@app.route('/control', methods=['POST'])
def control():
    data = request.json
    task_desc = data.get('task_description', 'Unknown task')
    
    # Start trace
    trace_id = tracer.start_trace(task_desc)
    tracer.log_event("controller", "task_received", {"task": task_desc}, trace_id)
    
    try:
        # Your existing code here...
        result = generate_control_sequence(task_desc, scene_info)
        
        # Log success
        tracer.log_event("controller", "task_completed", {"result": "success"}, trace_id)
        tracer.end_trace("completed", trace_id)
        
        return jsonify(result)
        
    except Exception as e:
        # Log error
        tracer.log_event("controller", "task_failed", {"error": str(e)}, trace_id)
        tracer.end_trace("error", trace_id)
        raise
```

### 4. Track LLM Costs

After each OpenAI API call, log the cost:

```python
# After calling OpenAI API
response = openai_client.chat.completions.create(
    model=config["openai"]["model"],
    messages=prompt["messages"],
    # ... other params
)

# Extract token usage
usage = response.usage
cost_tracker.log_api_call(
    model=config["openai"]["model"],
    input_tokens=usage.prompt_tokens,
    output_tokens=usage.completion_tokens,
    agent_name="controller",
    trace_id=trace_id
)

# Log the event
tracer.log_event("controller", "llm_call", {
    "model": config["openai"]["model"],
    "input_tokens": usage.prompt_tokens,
    "output_tokens": usage.completion_tokens
}, trace_id)
```

## 📝 Complete Integration Example

Here's a complete example for the controller's main function:

```python
def generate_control_sequence(task_desc: str, scene_info: dict, task_type: str = 'default', trace_id: str = None) -> dict:
    """Generate control sequence with monitoring"""
    global openai_client
    
    try:
        # Log start
        tracer.log_event("controller", "sequence_generation_start", {
            "task": task_desc,
            "task_type": task_type
        }, trace_id)
        
        # Build prompt via prompt service
        tracer.log_event("controller", "calling_prompt_service", {}, trace_id)
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
        
        tracer.log_event("controller", "prompt_built", {
            "prompt_length": len(str(prompt))
        }, trace_id)
        
        # Call LLM
        tracer.log_event("controller", "calling_llm", {
            "model": config["openai"]["model"]
        }, trace_id)
        
        start_time = time.time()
        response = openai_client.chat.completions.create(
            model=config["openai"]["model"],
            messages=prompt["messages"],
            temperature=0.7,
            max_tokens=12800,
            response_format={"type": "json_object"}
        )
        llm_duration = time.time() - start_time
        
        # Track cost
        usage = response.usage
        cost_entry = cost_tracker.log_api_call(
            model=config["openai"]["model"],
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            agent_name="controller",
            trace_id=trace_id
        )
        
        tracer.log_event("controller", "llm_response_received", {
            "duration": llm_duration,
            "input_tokens": usage.prompt_tokens,
            "output_tokens": usage.completion_tokens,
            "cost": cost_entry["total_cost"]
        }, trace_id)
        
        # Parse response
        output = response.choices[0].message.content
        control_plan = json.loads(output)
        
        tracer.log_event("controller", "sequence_generated", {
            "num_actions": len(control_plan.get("actions", []))
        }, trace_id)
        
        return control_plan
        
    except Exception as e:
        tracer.log_event("controller", "sequence_generation_error", {
            "error": str(e)
        }, trace_id)
        raise
```

## 🎯 Integration for Other Agents

### Detector Integration (`detector/app.py`)

```python
from utils.monitoring import tracer

@app.route('/detect', methods=['POST'])
def detect():
    trace_id = request.json.get('trace_id')
    
    tracer.log_event("detector", "detection_start", {}, trace_id)
    
    # Your detection code...
    results = get_florence_detection(model, processor, image, text_prompt)
    
    tracer.log_event("detector", "detection_complete", {
        "objects_found": len(results)
    }, trace_id)
    
    return jsonify(results)
```

### Grasper Integration (`grasper/app.py`)

```python
from utils.monitoring import tracer

@app.route('/grasp', methods=['POST'])
def compute_grasp():
    trace_id = request.json.get('trace_id')
    
    tracer.log_event("grasper", "grasp_computation_start", {}, trace_id)
    
    # Your grasp computation code...
    grasp_pose = compute_grasp_pose(point_cloud, object_mask)
    
    tracer.log_event("grasper", "grasp_computed", {
        "grasp_quality": grasp_pose.get("quality", 0)
    }, trace_id)
    
    return jsonify(grasp_pose)
```

## 📊 Dashboard Features

The monitoring dashboard provides:

### Real-time Metrics
- **GPU Usage**: Memory, utilization, temperature
- **CPU/Memory**: System resource usage
- **Live Updates**: Auto-refresh every 5 seconds

### Cost Tracking
- **Total Costs**: Last 24 hours
- **Per Model**: Breakdown by GPT model
- **Per Agent**: Cost attribution
- **Token Usage**: Input/output token counts

### Execution Traces
- **Task Flow**: See how tasks flow through agents
- **Timing**: Duration of each step
- **Events**: Detailed event log
- **Status**: Success/error tracking

### Historical Data
- **GPU History**: Last 10 minutes
- **Trends**: Average and peak usage
- **Samples**: Number of data points collected

## 🔧 Advanced Usage

### Custom Trace Events

```python
# Log custom events with rich data
tracer.log_event("controller", "custom_event", {
    "metric1": 123,
    "metric2": "value",
    "nested": {"data": "here"}
}, trace_id)
```

### Export Monitoring Data

```python
# Save GPU samples to file
gpu_monitor.save_samples("gpu_data_experiment1.json")

# Get cost summary for specific trace
cost_summary = cost_tracker.get_summary(trace_id="trace_20250115_143022")
print(f"Total cost: ${cost_summary['total_cost']}")

# Get trace details
trace_summary = tracer.get_trace_summary(trace_id)
print(f"Duration: {trace_summary['duration']}s")
print(f"Events: {trace_summary['total_events']}")
```

### Programmatic Access

```python
from utils.monitoring import tracer, cost_tracker, gpu_monitor

# Get current GPU stats
gpu_stats = gpu_monitor.get_current_stats()
print(f"GPU Memory: {gpu_stats['gpus'][0]['memory_used']}")

# Get cost summary for last hour
cost_summary = cost_tracker.get_summary(hours=1)
print(f"Last hour cost: ${cost_summary['total_cost']}")

# List all traces
for trace in tracer.traces:
    print(f"{trace['trace_id']}: {trace['task_description']}")
```

## 📈 Monitoring Best Practices

### 1. Always Pass trace_id
Pass the trace_id through all service calls:

```python
# In controller
trace_id = tracer.start_trace(task_desc)

# Pass to detector
detector_response = requests.post(detector_url, json={
    "image": image_data,
    "trace_id": trace_id  # ← Pass it along
})

# Pass to grasper
grasper_response = requests.post(grasper_url, json={
    "point_cloud": pc_data,
    "trace_id": trace_id  # ← Pass it along
})
```

### 2. Log Important Events
Log key milestones:

```python
tracer.log_event("agent_name", "event_type", {
    "relevant": "data",
    "metrics": 123
}, trace_id)
```

### 3. Track All LLM Calls
Always log API costs:

```python
cost_tracker.log_api_call(
    model=model_name,
    input_tokens=usage.prompt_tokens,
    output_tokens=usage.completion_tokens,
    agent_name="controller",
    trace_id=trace_id
)
```

### 4. Handle Errors Gracefully
Always end traces, even on error:

```python
try:
    # Your code
    tracer.end_trace("completed", trace_id)
except Exception as e:
    tracer.end_trace("error", trace_id)
    raise
```

## 🎨 Dashboard Customization

The dashboard is a single HTML file in `monitoring_dashboard.py`. You can customize:

- **Refresh interval**: Change `setInterval(loadAllData, 5000)` (milliseconds)
- **Colors**: Modify CSS gradient and colors
- **Metrics**: Add new API endpoints and display sections
- **Time ranges**: Adjust default time windows (24h, 10min, etc.)

## 🐛 Troubleshooting

### GPU Monitoring Not Working
```bash
# Install GPUtil
pip install gputil

# Check if GPUs are detected
python -c "import GPUtil; print(GPUtil.getGPUs())"
```

### Dashboard Not Loading
```bash
# Check if port 5000 is available
lsof -i :5000

# Use different port
python monitoring_dashboard.py --port 5001
```

### Traces Not Appearing
```python
# Make sure you're starting traces
trace_id = tracer.start_trace("My task")

# And ending them
tracer.end_trace("completed", trace_id)

# Check trace files
ls logs/traces/
```

## 📚 API Reference

### Tracer Methods
- `start_trace(task_description)` → trace_id
- `log_event(agent_name, event_type, data, trace_id)`
- `end_trace(status, trace_id)`
- `get_trace_summary(trace_id)` → dict

### Cost Tracker Methods
- `log_api_call(model, input_tokens, output_tokens, agent_name, trace_id)` → cost_entry
- `get_summary(trace_id, hours)` → dict

### GPU Monitor Methods
- `start_monitoring(interval)`
- `stop_monitoring()`
- `get_current_stats()` → dict
- `get_summary(minutes)` → dict
- `save_samples(filename)`

## 🎯 Next Steps

1. ✅ Install dependencies: `pip install gputil psutil`
2. ✅ Start dashboard: `python monitoring_dashboard.py`
3. ✅ Integrate into controller (see examples above)
4. ✅ Integrate into detector and grasper
5. ✅ Run a test task and view traces
6. ✅ Monitor costs and optimize

## 💡 Tips for Presentation

When presenting the monitoring system:

1. **Show the dashboard live** - Run it during demo
2. **Explain the value** - "See exactly where time/money is spent"
3. **Highlight insights** - "This task cost $0.05 and took 3.2 seconds"
4. **Show GPU usage** - "Peak memory usage was 8GB during detection"
5. **Demonstrate tracing** - "Here's the exact flow through all agents"

The monitoring system makes your project look **professional** and **production-ready**! 🚀
