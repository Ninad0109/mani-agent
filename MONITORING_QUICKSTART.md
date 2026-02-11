# 🚀 Monitoring Quick Start (5 Minutes)

Get execution tracing, cost tracking, and GPU monitoring running in 5 minutes!

## Step 1: Install Dependencies (1 min)

```bash
pip install gputil psutil
```

## Step 2: Start the Dashboard (30 seconds)

```bash
python monitoring_dashboard.py
```

You should see:
```
🚀 Starting ManiAgent Monitoring Dashboard
📊 Dashboard URL: http://localhost:5000
💡 Starting GPU monitoring...
✅ Ready! Open http://localhost:5000 in your browser
```

## Step 3: Open Dashboard (30 seconds)

Open your browser and go to: **http://localhost:5000**

You'll see a beautiful dashboard with:
- 🖥️ **GPU Stats** (real-time memory, utilization, temperature)
- 💰 **Cost Summary** (API costs for last 24 hours)
- 📊 **Recent Traces** (execution history)
- 📈 **GPU History** (last 10 minutes)

## Step 4: Test It! (3 minutes)

### Option A: Run the Test Script

```bash
cd utils
python monitoring.py
```

This will:
- Create a sample trace
- Log fake API costs
- Show GPU stats
- Display summaries

### Option B: Integrate into Your Code

Add to the top of `controller/app.py`:

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.monitoring import tracer, cost_tracker, gpu_monitor

# Start GPU monitoring
gpu_monitor.start_monitoring(interval=2.0)
```

Then wrap your main endpoint:

```python
@app.route('/control', methods=['POST'])
def control():
    data = request.json
    task = data.get('task_description', 'Unknown')
    
    # Start tracing
    trace_id = tracer.start_trace(task)
    tracer.log_event("controller", "task_received", {"task": task}, trace_id)
    
    try:
        # Your existing code...
        result = your_function(task)
        
        # End trace
        tracer.end_trace("completed", trace_id)
        return jsonify(result)
        
    except Exception as e:
        tracer.end_trace("error", trace_id)
        raise
```

## Step 5: View Results (30 seconds)

Refresh the dashboard (http://localhost:5000) and you'll see:
- ✅ Your trace in "Recent Execution Traces"
- ✅ GPU usage updating in real-time
- ✅ Costs accumulating (if you logged API calls)

## 🎯 What You Get

### 1. Execution Tracing
See exactly what happens during each task:
```json
{
  "trace_id": "trace_20250115_143022",
  "task": "Stack green cube on yellow cube",
  "duration": 3.45,
  "events": [
    {"agent": "controller", "event": "task_received"},
    {"agent": "detector", "event": "detection_complete"},
    {"agent": "grasper", "event": "grasp_computed"}
  ]
}
```

### 2. Cost Tracking
Know exactly how much each task costs:
```
Total Cost: $0.0234
- GPT-4o: $0.0200 (1 call)
- GPT-4o-mini: $0.0034 (2 calls)
```

### 3. GPU Monitoring
Real-time resource usage:
```
GPU 0 (NVIDIA RTX 3090)
- Memory: 8.2 GB / 24 GB (34%)
- Utilization: 67%
- Temperature: 72°C
```

## 📊 Dashboard Features

### Auto-Refresh
Dashboard updates every 5 seconds automatically. No need to refresh!

### Live Indicators
Green pulsing dot = monitoring is active

### Color-Coded Status
- 🟢 Green = Running
- 🔵 Blue = Completed
- 🔴 Red = Error

### Responsive Design
Works on desktop, tablet, and mobile!

## 🔧 Common Issues

### "GPU monitoring unavailable"
**Solution**: Install GPUtil
```bash
pip install gputil
```

### "Port 5000 already in use"
**Solution**: Use a different port
```bash
# Edit monitoring_dashboard.py, change last line:
app.run(host='0.0.0.0', port=5001, debug=False)
```

### "No traces yet"
**Solution**: Make sure you're calling `tracer.start_trace()` in your code

## 🎨 Customization

### Change Refresh Rate
Edit `monitoring_dashboard.py`:
```javascript
// Change from 5000ms (5 sec) to 2000ms (2 sec)
setInterval(loadAllData, 2000);
```

### Change GPU Sampling Rate
```python
# In your code
gpu_monitor.start_monitoring(interval=1.0)  # Sample every 1 second
```

### Change Time Windows
```javascript
// In dashboard, change API calls:
fetch('/api/costs/summary?hours=1')  // Last 1 hour instead of 24
fetch('/api/gpu/summary?minutes=5')  // Last 5 min instead of 10
```

## 📈 For Your Presentation

### Show This Flow:

1. **Open Dashboard** → "Here's our real-time monitoring system"
2. **Run a Task** → "Let's stack some blocks"
3. **Watch Updates** → "See the GPU usage spike during detection"
4. **Show Trace** → "Here's the exact execution flow"
5. **Show Costs** → "This task cost $0.05"

### Key Talking Points:

✅ "We track every step of execution"  
✅ "We monitor API costs in real-time"  
✅ "We measure GPU/CPU resource usage"  
✅ "Everything is logged for debugging"  
✅ "Dashboard updates automatically"

## 🚀 Next Steps

1. ✅ **Integrate into all agents** - See `MONITORING_INTEGRATION.md`
2. ✅ **Add custom events** - Log domain-specific metrics
3. ✅ **Export data** - Save traces and GPU samples for analysis
4. ✅ **Set up alerts** - Monitor costs and resource usage

## 💡 Pro Tips

### Tip 1: Pass trace_id Everywhere
```python
# In controller
trace_id = tracer.start_trace(task)

# Pass to detector
requests.post(detector_url, json={"trace_id": trace_id, ...})

# Pass to grasper
requests.post(grasper_url, json={"trace_id": trace_id, ...})
```

### Tip 2: Log Rich Data
```python
tracer.log_event("detector", "objects_found", {
    "count": 3,
    "objects": ["green_cube", "yellow_cube", "table"],
    "confidence": [0.95, 0.92, 0.88]
}, trace_id)
```

### Tip 3: Track All LLM Calls
```python
# After every OpenAI call
cost_tracker.log_api_call(
    model="gpt-4o",
    input_tokens=response.usage.prompt_tokens,
    output_tokens=response.usage.completion_tokens,
    agent_name="controller",
    trace_id=trace_id
)
```

## 🎉 You're Done!

You now have:
- ✅ Real-time monitoring dashboard
- ✅ Execution tracing
- ✅ Cost tracking
- ✅ GPU monitoring
- ✅ Professional-looking metrics

**Time to impress in your presentation! 🚀**

---

**Need help?** Check `MONITORING_INTEGRATION.md` for detailed integration examples.
