# 🔍 ManiAgent Monitoring System

> **Professional execution tracing, cost tracking, and GPU monitoring for ManiAgent**

## 🎯 What You Get

This monitoring system adds **production-grade observability** to ManiAgent:

| Feature | What It Does | Why It Matters |
|---------|-------------|----------------|
| **📊 Execution Tracing** | Tracks every step through all agents | Debug issues, understand flow |
| **💰 Cost Tracking** | Monitors API costs per task/model/agent | Control spending, optimize costs |
| **🖥️ GPU Monitoring** | Real-time GPU/CPU/memory usage | Optimize resources, prevent OOM |
| **📈 Historical Data** | Stores all metrics for analysis | Identify trends, improve performance |
| **🎨 Live Dashboard** | Beautiful web UI with auto-refresh | Monitor in real-time during demos |

## 🚀 Quick Start (5 Minutes)

### 1. Install
```bash
pip install gputil psutil
```

### 2. Start Dashboard
```bash
python monitoring_dashboard.py
```

### 3. Open Browser
Go to: **http://localhost:5000**

### 4. See It Work!
Run any ManiAgent task and watch the dashboard update in real-time!

📖 **Detailed Guide**: See [MONITORING_QUICKSTART.md](MONITORING_QUICKSTART.md)

## 📸 Dashboard Preview

The dashboard shows:

```
┌─────────────────────────────────────────────────────────┐
│  🤖 ManiAgent Monitoring Dashboard                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ GPU Stats    │  │ Cost Summary │  │ Recent Traces│ │
│  │              │  │              │  │              │ │
│  │ Memory: 34%  │  │ $0.0234      │  │ Stack blocks │ │
│  │ Util: 67%    │  │ 3 calls      │  │ ✓ 3.45s      │ │
│  │ Temp: 72°C   │  │ 1.2K tokens  │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ GPU Usage History (Last 10 min)                    │ │
│  │ Avg: 45% | Max: 78% | Samples: 300                │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Your Application                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Controller│  │ Detector │  │ Grasper  │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │             │                     │
│       └─────────────┴─────────────┘                     │
│                     │                                    │
│              ┌──────▼──────┐                            │
│              │ Monitoring  │                            │
│              │   System    │                            │
│              └──────┬──────┘                            │
│                     │                                    │
│       ┌─────────────┼─────────────┐                    │
│       │             │             │                     │
│  ┌────▼────┐  ┌────▼────┐  ┌────▼────┐                │
│  │ Tracer  │  │  Cost   │  │   GPU   │                │
│  │         │  │ Tracker │  │ Monitor │                │
│  └────┬────┘  └────┬────┘  └────┬────┘                │
│       │            │            │                       │
│       └────────────┴────────────┘                       │
│                    │                                     │
│              ┌─────▼─────┐                              │
│              │ Dashboard │                              │
│              │   (Web)   │                              │
│              └───────────┘                              │
└─────────────────────────────────────────────────────────┘
```

## 📦 Components

### 1. Execution Tracer (`utils/monitoring.py`)
Tracks the flow of execution across all agents:

```python
from utils.monitoring import tracer

# Start a trace
trace_id = tracer.start_trace("Stack green cube on yellow cube")

# Log events
tracer.log_event("controller", "task_received", {"task": "stack"}, trace_id)
tracer.log_event("detector", "objects_found", {"count": 2}, trace_id)
tracer.log_event("grasper", "grasp_computed", {"quality": 0.95}, trace_id)

# End trace
tracer.end_trace("completed", trace_id)
```

**Output**: JSON trace file with complete execution history

### 2. Cost Tracker (`utils/monitoring.py`)
Monitors API costs for all LLM calls:

```python
from utils.monitoring import cost_tracker

# Log an API call
cost_tracker.log_api_call(
    model="gpt-4o",
    input_tokens=1000,
    output_tokens=500,
    agent_name="controller",
    trace_id=trace_id
)

# Get summary
summary = cost_tracker.get_summary(hours=24)
print(f"Total cost: ${summary['total_cost']}")
```

**Output**: Cost breakdown by model, agent, and time period

### 3. GPU Monitor (`utils/monitoring.py`)
Tracks GPU/CPU/memory usage:

```python
from utils.monitoring import gpu_monitor

# Start monitoring
gpu_monitor.start_monitoring(interval=2.0)

# Get current stats
stats = gpu_monitor.get_current_stats()
print(f"GPU Memory: {stats['gpus'][0]['memory_used']}")

# Get summary
summary = gpu_monitor.get_summary(minutes=10)
print(f"Avg GPU util: {summary['gpu']['avg_gpu_util']}%")
```

**Output**: Real-time and historical GPU/CPU metrics

### 4. Dashboard (`monitoring_dashboard.py`)
Web interface for visualization:

```bash
python monitoring_dashboard.py
# Opens on http://localhost:5000
```

**Features**:
- Auto-refresh every 5 seconds
- Real-time GPU stats
- Cost summaries
- Execution traces
- Historical charts

## 🔧 Integration

### Basic Integration (3 lines)

```python
from utils.monitoring import tracer, cost_tracker, gpu_monitor

# Start GPU monitoring
gpu_monitor.start_monitoring(interval=2.0)

# Wrap your endpoint
@app.route('/control', methods=['POST'])
def control():
    trace_id = tracer.start_trace(request.json['task'])
    try:
        result = your_function()
        tracer.end_trace("completed", trace_id)
        return jsonify(result)
    except Exception as e:
        tracer.end_trace("error", trace_id)
        raise
```

### Full Integration

See [MONITORING_INTEGRATION.md](MONITORING_INTEGRATION.md) for:
- Complete controller integration
- Detector integration
- Grasper integration
- Cost tracking for LLM calls
- Custom event logging
- Error handling

## 📊 Use Cases

### 1. Debugging
**Problem**: Task fails, don't know where  
**Solution**: Check trace to see exact failure point

```python
trace = tracer.get_trace_summary(trace_id)
# Shows: Failed at "grasper" agent, event "grasp_computation"
```

### 2. Cost Optimization
**Problem**: API costs too high  
**Solution**: Identify expensive calls

```python
summary = cost_tracker.get_summary(hours=24)
# Shows: GPT-4o costs $2.50, GPT-4o-mini costs $0.10
# Action: Switch to mini for simple tasks
```

### 3. Performance Tuning
**Problem**: Tasks running slow  
**Solution**: Check GPU utilization

```python
summary = gpu_monitor.get_summary(minutes=10)
# Shows: GPU only 30% utilized
# Action: Increase batch size or use smaller model
```

### 4. Resource Planning
**Problem**: Need to estimate infrastructure costs  
**Solution**: Analyze historical data

```python
# Run 100 tasks, then:
summary = cost_tracker.get_summary()
avg_cost = summary['average_cost_per_call']
# Estimate: 10,000 tasks/month = $avg_cost * 10,000
```

## 📈 Metrics Collected

### Execution Metrics
- Task duration
- Events per agent
- Success/failure rate
- Event timestamps
- Agent call sequence

### Cost Metrics
- Total API cost
- Cost per model
- Cost per agent
- Token usage (input/output)
- Average cost per call

### Resource Metrics
- GPU memory usage
- GPU utilization
- GPU temperature
- CPU usage
- System memory usage
- Sampling frequency

## 🎨 Dashboard Features

### Real-Time Updates
- Auto-refresh every 5 seconds
- Live GPU stats
- Pulsing indicator for active monitoring

### Visual Design
- Color-coded status badges
- Progress bars for GPU usage
- Gradient backgrounds
- Responsive layout

### Time Windows
- Costs: Last 24 hours
- GPU history: Last 10 minutes
- Traces: Last 5 traces
- Customizable via API parameters

## 🔌 API Endpoints

The dashboard exposes REST APIs:

```bash
# Current GPU stats
GET /api/gpu/current

# GPU summary (last N minutes)
GET /api/gpu/summary?minutes=10

# Cost summary (last N hours)
GET /api/costs/summary?hours=24

# List recent traces
GET /api/traces/list?limit=10

# Get specific trace
GET /api/traces/<trace_id>

# Health check
GET /health
```

## 💾 Data Storage

### Traces
- Location: `logs/traces/`
- Format: JSON
- Filename: `trace_YYYYMMDD_HHMMSS_ffffff.json`
- Retention: Manual cleanup

### Costs
- Location: `logs/costs/`
- Format: JSONL (one entry per line)
- Filename: `costs_YYYYMMDD.jsonl`
- Retention: Daily files

### GPU Samples
- Location: `logs/gpu/`
- Format: JSON
- Filename: Custom via `save_samples()`
- Retention: Manual save

## 🎯 For Presentations

### Demo Flow

1. **Start Dashboard** (30 sec)
   ```bash
   python monitoring_dashboard.py
   ```

2. **Show Empty State** (10 sec)
   - "Here's our monitoring system"
   - "Currently no tasks running"

3. **Run a Task** (2 min)
   ```bash
   # Run your ManiAgent task
   python controller/app.py
   # Execute task via API
   ```

4. **Show Live Updates** (1 min)
   - GPU usage spikes during detection
   - Trace appears in dashboard
   - Cost accumulates

5. **Explain Insights** (1 min)
   - "This task cost $0.05"
   - "Peak GPU usage was 8GB"
   - "Took 3.2 seconds total"
   - "Detector was the bottleneck"

### Key Talking Points

✅ **Professional**: "Production-grade monitoring system"  
✅ **Real-time**: "Updates every 5 seconds automatically"  
✅ **Comprehensive**: "Tracks execution, costs, and resources"  
✅ **Actionable**: "Helps optimize performance and costs"  
✅ **Easy to use**: "Just 3 lines of code to integrate"

## 🐛 Troubleshooting

### GPU Monitoring Not Working
```bash
# Check if GPUtil is installed
pip install gputil

# Test GPU detection
python -c "import GPUtil; print(GPUtil.getGPUs())"
```

### Dashboard Not Loading
```bash
# Check if port 5000 is free
lsof -i :5000

# Kill process if needed
kill -9 <PID>

# Or use different port
# Edit monitoring_dashboard.py: app.run(port=5001)
```

### No Traces Appearing
```python
# Make sure you're starting and ending traces
trace_id = tracer.start_trace("My task")
# ... your code ...
tracer.end_trace("completed", trace_id)

# Check trace files
ls logs/traces/
```

### Costs Not Tracking
```python
# Make sure you're logging API calls
cost_tracker.log_api_call(
    model="gpt-4o",
    input_tokens=response.usage.prompt_tokens,
    output_tokens=response.usage.completion_tokens,
    agent_name="controller",
    trace_id=trace_id
)
```

## 📚 Documentation

- **Quick Start**: [MONITORING_QUICKSTART.md](MONITORING_QUICKSTART.md) - Get running in 5 minutes
- **Integration Guide**: [MONITORING_INTEGRATION.md](MONITORING_INTEGRATION.md) - Detailed integration examples
- **API Reference**: See docstrings in `utils/monitoring.py`

## 🎓 Learning Resources

### Example Traces
```json
{
  "trace_id": "trace_20250115_143022_123456",
  "task_description": "Stack green cube on yellow cube",
  "start_time": 1705329022.123,
  "end_time": 1705329025.567,
  "duration": 3.444,
  "status": "completed",
  "events": [
    {
      "timestamp": 1705329022.234,
      "agent": "controller",
      "event_type": "task_received",
      "data": {"task": "stack blocks"}
    },
    {
      "timestamp": 1705329023.456,
      "agent": "detector",
      "event_type": "detection_complete",
      "data": {"objects_found": 2}
    },
    {
      "timestamp": 1705329024.789,
      "agent": "grasper",
      "event_type": "grasp_computed",
      "data": {"grasp_quality": 0.95}
    }
  ]
}
```

### Example Cost Summary
```json
{
  "total_cost": 0.0234,
  "total_calls": 3,
  "total_tokens": 1500,
  "by_model": {
    "gpt-4o": {
      "calls": 1,
      "cost": 0.0200,
      "tokens": 1000
    },
    "gpt-4o-mini": {
      "calls": 2,
      "cost": 0.0034,
      "tokens": 500
    }
  },
  "by_agent": {
    "controller": {
      "calls": 2,
      "cost": 0.0220,
      "tokens": 1200
    },
    "detector": {
      "calls": 1,
      "cost": 0.0014,
      "tokens": 300
    }
  }
}
```

## 🚀 Advanced Features

### Custom Events
```python
tracer.log_event("my_agent", "custom_event", {
    "metric1": 123,
    "metric2": "value",
    "nested": {"data": "here"}
}, trace_id)
```

### Export Data
```python
# Save GPU samples
gpu_monitor.save_samples("experiment1_gpu.json")

# Get trace for analysis
trace = tracer.get_trace_summary(trace_id)

# Export costs
summary = cost_tracker.get_summary(hours=24)
```

### Programmatic Access
```python
# Get all traces
for trace in tracer.traces:
    print(f"{trace['trace_id']}: {trace['duration']}s")

# Get all costs
for cost in cost_tracker.costs:
    print(f"{cost['model']}: ${cost['total_cost']}")
```

## 🎉 Benefits

### For Development
- ✅ Debug issues faster
- ✅ Understand execution flow
- ✅ Identify bottlenecks
- ✅ Optimize performance

### For Production
- ✅ Monitor costs in real-time
- ✅ Track resource usage
- ✅ Detect anomalies
- ✅ Plan capacity

### For Presentations
- ✅ Professional appearance
- ✅ Live demonstrations
- ✅ Data-driven insights
- ✅ Impressive metrics

## 📞 Support

- **Issues**: Open a GitHub issue
- **Questions**: Check [MONITORING_INTEGRATION.md](MONITORING_INTEGRATION.md)
- **Examples**: See `utils/monitoring.py` test code

---

**Made with ❤️ for ManiAgent**

*Transform your robot manipulation framework into a production-ready system with professional monitoring!*
