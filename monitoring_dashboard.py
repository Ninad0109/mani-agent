"""
Monitoring Dashboard for ManiAgent
Provides REST API endpoints for real-time monitoring
Run with: python monitoring_dashboard.py
Access at: http://localhost:5000
"""

from flask import Flask, jsonify, render_template_string, request
import sys
import os

# Add utils to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.monitoring import tracer, cost_tracker, gpu_monitor

app = Flask(__name__)

# HTML Dashboard Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ManiAgent Monitoring Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-label {
            color: #666;
            font-weight: 500;
        }
        .metric-value {
            color: #333;
            font-weight: bold;
            font-size: 1.1em;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        .status-running { background: #4ade80; color: white; }
        .status-completed { background: #3b82f6; color: white; }
        .status-error { background: #ef4444; color: white; }
        .refresh-btn {
            background: white;
            color: #667eea;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            display: block;
            margin: 20px auto;
        }
        .refresh-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        .loading {
            text-align: center;
            color: white;
            font-size: 1.2em;
            margin: 50px 0;
        }
        .trace-list {
            max-height: 400px;
            overflow-y: auto;
        }
        .trace-item {
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .trace-item h4 {
            color: #667eea;
            margin-bottom: 8px;
        }
        .cost-highlight {
            font-size: 2em;
            color: #667eea;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }
        .gpu-bar {
            background: #e5e7eb;
            height: 25px;
            border-radius: 12px;
            overflow: hidden;
            margin: 10px 0;
        }
        .gpu-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #4ade80, #22c55e);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
        }
        .error-message {
            background: #fee2e2;
            color: #991b1b;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .live-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #4ade80;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 ManiAgent Monitoring Dashboard</h1>
        
        <button class="refresh-btn" onclick="loadAllData()">
            🔄 Refresh All Data
        </button>
        
        <div class="grid">
            <!-- GPU Stats -->
            <div class="card">
                <h2><span class="live-indicator"></span>GPU & System Stats</h2>
                <div id="gpu-stats">
                    <div class="loading">Loading...</div>
                </div>
            </div>
            
            <!-- Cost Summary -->
            <div class="card">
                <h2>💰 Cost Summary (Last 24h)</h2>
                <div id="cost-summary">
                    <div class="loading">Loading...</div>
                </div>
            </div>
            
            <!-- Recent Traces -->
            <div class="card">
                <h2>📊 Recent Execution Traces</h2>
                <div id="traces">
                    <div class="loading">Loading...</div>
                </div>
            </div>
        </div>
        
        <!-- GPU History -->
        <div class="card">
            <h2>📈 GPU Usage History (Last 10 min)</h2>
            <div id="gpu-history">
                <div class="loading">Loading...</div>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 5 seconds
        setInterval(loadAllData, 5000);
        
        // Load on page load
        window.onload = loadAllData;
        
        function loadAllData() {
            loadGPUStats();
            loadCostSummary();
            loadTraces();
            loadGPUHistory();
        }
        
        async function loadGPUStats() {
            try {
                const response = await fetch('/api/gpu/current');
                const data = await response.json();
                
                let html = '';
                
                if (data.error) {
                    html = `<div class="error-message">${data.error}</div>`;
                } else {
                    // GPU info
                    if (data.gpus && data.gpus.length > 0) {
                        data.gpus.forEach(gpu => {
                            html += `
                                <div style="margin-bottom: 20px;">
                                    <h4>${gpu.name} (GPU ${gpu.gpu_id})</h4>
                                    <div class="metric">
                                        <span class="metric-label">Memory Usage</span>
                                        <span class="metric-value">${gpu.memory_used} / ${gpu.memory_total}</span>
                                    </div>
                                    <div class="gpu-bar">
                                        <div class="gpu-bar-fill" style="width: ${gpu.memory_util}">${gpu.memory_util}</div>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">GPU Utilization</span>
                                        <span class="metric-value">${gpu.gpu_util}</span>
                                    </div>
                                    <div class="gpu-bar">
                                        <div class="gpu-bar-fill" style="width: ${gpu.gpu_util}">${gpu.gpu_util}</div>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">Temperature</span>
                                        <span class="metric-value">${gpu.temperature}</span>
                                    </div>
                                </div>
                            `;
                        });
                    }
                    
                    // CPU info
                    if (data.cpu) {
                        html += `
                            <div style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #eee;">
                                <h4>System Resources</h4>
                                <div class="metric">
                                    <span class="metric-label">CPU Usage</span>
                                    <span class="metric-value">${data.cpu.cpu_percent}</span>
                                </div>
                                <div class="metric">
                                    <span class="metric-label">Memory Usage</span>
                                    <span class="metric-value">${data.cpu.memory_used} (${data.cpu.memory_percent})</span>
                                </div>
                            </div>
                        `;
                    }
                }
                
                document.getElementById('gpu-stats').innerHTML = html;
            } catch (error) {
                document.getElementById('gpu-stats').innerHTML = 
                    `<div class="error-message">Error loading GPU stats: ${error.message}</div>`;
            }
        }
        
        async function loadCostSummary() {
            try {
                const response = await fetch('/api/costs/summary?hours=24');
                const data = await response.json();
                
                let html = `
                    <div class="cost-highlight">$${data.total_cost.toFixed(4)}</div>
                    <div class="metric">
                        <span class="metric-label">Total API Calls</span>
                        <span class="metric-value">${data.total_calls}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Tokens</span>
                        <span class="metric-value">${data.total_tokens.toLocaleString()}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Avg Cost/Call</span>
                        <span class="metric-value">$${data.average_cost_per_call.toFixed(4)}</span>
                    </div>
                `;
                
                if (data.by_model) {
                    html += '<h4 style="margin-top: 20px; color: #667eea;">By Model</h4>';
                    for (const [model, stats] of Object.entries(data.by_model)) {
                        html += `
                            <div class="metric">
                                <span class="metric-label">${model}</span>
                                <span class="metric-value">$${stats.cost.toFixed(4)} (${stats.calls} calls)</span>
                            </div>
                        `;
                    }
                }
                
                document.getElementById('cost-summary').innerHTML = html;
            } catch (error) {
                document.getElementById('cost-summary').innerHTML = 
                    `<div class="error-message">Error loading costs: ${error.message}</div>`;
            }
        }
        
        async function loadTraces() {
            try {
                const response = await fetch('/api/traces/list?limit=5');
                const data = await response.json();
                
                if (data.traces.length === 0) {
                    document.getElementById('traces').innerHTML = 
                        '<p style="color: #999; text-align: center;">No traces yet</p>';
                    return;
                }
                
                let html = '<div class="trace-list">';
                data.traces.forEach(trace => {
                    const statusClass = `status-${trace.status}`;
                    html += `
                        <div class="trace-item">
                            <h4>${trace.task}</h4>
                            <div class="metric">
                                <span class="metric-label">Status</span>
                                <span class="status-badge ${statusClass}">${trace.status}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Duration</span>
                                <span class="metric-value">${trace.duration.toFixed(2)}s</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Events</span>
                                <span class="metric-value">${trace.total_events}</span>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                
                document.getElementById('traces').innerHTML = html;
            } catch (error) {
                document.getElementById('traces').innerHTML = 
                    `<div class="error-message">Error loading traces: ${error.message}</div>`;
            }
        }
        
        async function loadGPUHistory() {
            try {
                const response = await fetch('/api/gpu/summary?minutes=10');
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('gpu-history').innerHTML = 
                        `<div class="error-message">${data.error}</div>`;
                    return;
                }
                
                let html = '';
                
                if (data.gpu) {
                    html += `
                        <div class="metric">
                            <span class="metric-label">Avg GPU Utilization</span>
                            <span class="metric-value">${data.gpu.avg_gpu_util}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Max GPU Utilization</span>
                            <span class="metric-value">${data.gpu.max_gpu_util}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Avg Memory Utilization</span>
                            <span class="metric-value">${data.gpu.avg_memory_util}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Max Memory Utilization</span>
                            <span class="metric-value">${data.gpu.max_memory_util}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Avg Temperature</span>
                            <span class="metric-value">${data.gpu.avg_temperature}°C</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Samples Collected</span>
                            <span class="metric-value">${data.gpu.samples_collected}</span>
                        </div>
                    `;
                }
                
                if (data.cpu) {
                    html += `
                        <h4 style="margin-top: 20px; color: #667eea;">CPU History</h4>
                        <div class="metric">
                            <span class="metric-label">Avg CPU Usage</span>
                            <span class="metric-value">${data.cpu.avg_cpu_percent}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Max CPU Usage</span>
                            <span class="metric-value">${data.cpu.max_cpu_percent}%</span>
                        </div>
                    `;
                }
                
                document.getElementById('gpu-history').innerHTML = html;
            } catch (error) {
                document.getElementById('gpu-history').innerHTML = 
                    `<div class="error-message">Error loading GPU history: ${error.message}</div>`;
            }
        }
    </script>
</body>
</html>
"""

# API Endpoints

@app.route('/')
def dashboard():
    """Serve the monitoring dashboard"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/gpu/current')
def get_gpu_current():
    """Get current GPU stats"""
    return jsonify(gpu_monitor.get_current_stats())

@app.route('/api/gpu/summary')
def get_gpu_summary():
    """Get GPU summary statistics"""
    minutes = request.args.get('minutes', type=int)
    return jsonify(gpu_monitor.get_summary(minutes=minutes))

@app.route('/api/costs/summary')
def get_cost_summary():
    """Get cost summary"""
    trace_id = request.args.get('trace_id')
    hours = request.args.get('hours', type=int)
    return jsonify(cost_tracker.get_summary(trace_id=trace_id, hours=hours))

@app.route('/api/traces/list')
def get_traces():
    """Get list of recent traces"""
    limit = request.args.get('limit', default=10, type=int)
    
    # Get recent traces
    recent_traces = []
    for trace in tracer.traces[-limit:]:
        summary = {
            "trace_id": trace["trace_id"],
            "task": trace["task_description"],
            "status": trace["status"],
            "duration": trace.get("duration", 0),
            "total_events": len(trace["events"])
        }
        recent_traces.append(summary)
    
    return jsonify({"traces": list(reversed(recent_traces))})

@app.route('/api/traces/<trace_id>')
def get_trace_detail(trace_id):
    """Get detailed trace information"""
    summary = tracer.get_trace_summary(trace_id)
    return jsonify(summary)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "monitoring": {
            "tracer": "active",
            "cost_tracker": "active",
            "gpu_monitor": "active" if gpu_monitor.monitoring else "inactive"
        }
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting ManiAgent Monitoring Dashboard")
    print("=" * 60)
    print("\n📊 Dashboard URL: http://localhost:5000")
    print("🔍 API Endpoints:")
    print("   - GET  /api/gpu/current")
    print("   - GET  /api/gpu/summary?minutes=10")
    print("   - GET  /api/costs/summary?hours=24")
    print("   - GET  /api/traces/list?limit=10")
    print("   - GET  /api/traces/<trace_id>")
    print("   - GET  /health")
    print("\n💡 Starting GPU monitoring...")
    
    # Start GPU monitoring
    gpu_monitor.start_monitoring(interval=2.0)
    
    print("✅ Ready! Open http://localhost:5000 in your browser\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        gpu_monitor.stop_monitoring()
        print("✅ Monitoring stopped. Goodbye!")
