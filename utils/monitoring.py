"""
Monitoring utilities for ManiAgent
Provides execution tracing, cost tracking, and GPU usage monitoring
"""

import time
import json
import os
from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional, Any
import threading
from collections import defaultdict

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    print("Warning: GPUtil not installed. GPU monitoring disabled. Install with: pip install gputil")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not installed. CPU/Memory monitoring disabled. Install with: pip install psutil")


class ExecutionTracer:
    """Tracks execution flow across agents"""
    
    def __init__(self, log_dir: str = "logs/traces"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.traces = []
        self.current_trace_id = None
        self.lock = threading.Lock()
        
    def start_trace(self, task_description: str) -> str:
        """Start a new execution trace"""
        trace_id = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        with self.lock:
            self.current_trace_id = trace_id
            self.traces.append({
                "trace_id": trace_id,
                "task_description": task_description,
                "start_time": time.time(),
                "events": [],
                "status": "running"
            })
        return trace_id
    
    def log_event(self, agent_name: str, event_type: str, data: Dict = None, trace_id: str = None):
        """Log an event in the current trace"""
        if trace_id is None:
            trace_id = self.current_trace_id
            
        if trace_id is None:
            print("Warning: No active trace. Call start_trace() first.")
            return
            
        event = {
            "timestamp": time.time(),
            "agent": agent_name,
            "event_type": event_type,
            "data": data or {}
        }
        
        with self.lock:
            for trace in self.traces:
                if trace["trace_id"] == trace_id:
                    trace["events"].append(event)
                    break
    
    def end_trace(self, status: str = "completed", trace_id: str = None):
        """End the current trace"""
        if trace_id is None:
            trace_id = self.current_trace_id
            
        with self.lock:
            for trace in self.traces:
                if trace["trace_id"] == trace_id:
                    trace["end_time"] = time.time()
                    trace["duration"] = trace["end_time"] - trace["start_time"]
                    trace["status"] = status
                    
                    # Save to file
                    trace_file = os.path.join(self.log_dir, f"{trace_id}.json")
                    with open(trace_file, 'w') as f:
                        json.dump(trace, f, indent=2)
                    
                    print(f"✅ Trace saved: {trace_file}")
                    break
            
            if trace_id == self.current_trace_id:
                self.current_trace_id = None
    
    def get_trace_summary(self, trace_id: str = None) -> Dict:
        """Get summary of a trace"""
        if trace_id is None:
            trace_id = self.current_trace_id
            
        with self.lock:
            for trace in self.traces:
                if trace["trace_id"] == trace_id:
                    events_by_agent = defaultdict(int)
                    for event in trace["events"]:
                        events_by_agent[event["agent"]] += 1
                    
                    return {
                        "trace_id": trace_id,
                        "task": trace["task_description"],
                        "duration": trace.get("duration", time.time() - trace["start_time"]),
                        "status": trace["status"],
                        "total_events": len(trace["events"]),
                        "events_by_agent": dict(events_by_agent)
                    }
        return {}


class CostTracker:
    """Tracks API costs for LLM calls"""
    
    # Pricing per 1M tokens (update these based on current pricing)
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.150, "output": 0.600},
        "gpt-5-nano-2025-08-07": {"input": 0.10, "output": 0.40},
        "gpt-5-2025-08-07": {"input": 5.00, "output": 15.00},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
    }
    
    def __init__(self, log_dir: str = "logs/costs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.costs = []
        self.lock = threading.Lock()
        
    def log_api_call(self, 
                     model: str, 
                     input_tokens: int, 
                     output_tokens: int,
                     agent_name: str = "unknown",
                     trace_id: str = None):
        """Log an API call and calculate cost"""
        
        # Get pricing for model
        pricing = self.PRICING.get(model, {"input": 0, "output": 0})
        
        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        cost_entry = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "trace_id": trace_id,
            "agent": agent_name,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }
        
        with self.lock:
            self.costs.append(cost_entry)
            
            # Save to daily log file
            date_str = datetime.now().strftime("%Y%m%d")
            cost_file = os.path.join(self.log_dir, f"costs_{date_str}.jsonl")
            with open(cost_file, 'a') as f:
                f.write(json.dumps(cost_entry) + "\n")
        
        return cost_entry
    
    def get_summary(self, trace_id: str = None, hours: int = None) -> Dict:
        """Get cost summary"""
        with self.lock:
            filtered_costs = self.costs
            
            # Filter by trace_id
            if trace_id:
                filtered_costs = [c for c in filtered_costs if c.get("trace_id") == trace_id]
            
            # Filter by time
            if hours:
                cutoff_time = time.time() - (hours * 3600)
                filtered_costs = [c for c in filtered_costs if c["timestamp"] > cutoff_time]
            
            if not filtered_costs:
                return {"total_cost": 0, "total_calls": 0}
            
            total_cost = sum(c["total_cost"] for c in filtered_costs)
            total_tokens = sum(c["total_tokens"] for c in filtered_costs)
            
            # Group by model
            by_model = defaultdict(lambda: {"calls": 0, "cost": 0, "tokens": 0})
            for cost in filtered_costs:
                model = cost["model"]
                by_model[model]["calls"] += 1
                by_model[model]["cost"] += cost["total_cost"]
                by_model[model]["tokens"] += cost["total_tokens"]
            
            # Group by agent
            by_agent = defaultdict(lambda: {"calls": 0, "cost": 0, "tokens": 0})
            for cost in filtered_costs:
                agent = cost["agent"]
                by_agent[agent]["calls"] += 1
                by_agent[agent]["cost"] += cost["total_cost"]
                by_agent[agent]["tokens"] += cost["total_tokens"]
            
            return {
                "total_cost": round(total_cost, 4),
                "total_calls": len(filtered_costs),
                "total_tokens": total_tokens,
                "by_model": dict(by_model),
                "by_agent": dict(by_agent),
                "average_cost_per_call": round(total_cost / len(filtered_costs), 4) if filtered_costs else 0
            }


class GPUMonitor:
    """Monitors GPU usage"""
    
    def __init__(self, log_dir: str = "logs/gpu"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.monitoring = False
        self.monitor_thread = None
        self.samples = []
        self.lock = threading.Lock()
        
        if not GPU_AVAILABLE:
            print("⚠️  GPU monitoring unavailable. Install GPUtil: pip install gputil")
    
    def start_monitoring(self, interval: float = 1.0):
        """Start continuous GPU monitoring"""
        if not GPU_AVAILABLE:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print(f"🔍 GPU monitoring started (interval: {interval}s)")
    
    def _monitor_loop(self, interval: float):
        """Internal monitoring loop"""
        while self.monitoring:
            try:
                gpus = GPUtil.getGPUs()
                timestamp = time.time()
                
                for gpu in gpus:
                    sample = {
                        "timestamp": timestamp,
                        "datetime": datetime.now().isoformat(),
                        "gpu_id": gpu.id,
                        "gpu_name": gpu.name,
                        "memory_used_mb": gpu.memoryUsed,
                        "memory_total_mb": gpu.memoryTotal,
                        "memory_util_percent": gpu.memoryUtil * 100,
                        "gpu_util_percent": gpu.load * 100,
                        "temperature_c": gpu.temperature
                    }
                    
                    with self.lock:
                        self.samples.append(sample)
                
                # Also log CPU/Memory if available
                if PSUTIL_AVAILABLE:
                    cpu_sample = {
                        "timestamp": timestamp,
                        "datetime": datetime.now().isoformat(),
                        "cpu_percent": psutil.cpu_percent(interval=None),
                        "memory_percent": psutil.virtual_memory().percent,
                        "memory_used_gb": psutil.virtual_memory().used / (1024**3)
                    }
                    with self.lock:
                        self.samples.append(cpu_sample)
                        
            except Exception as e:
                print(f"GPU monitoring error: {e}")
            
            time.sleep(interval)
    
    def stop_monitoring(self):
        """Stop GPU monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("🛑 GPU monitoring stopped")
    
    def get_current_stats(self) -> Dict:
        """Get current GPU statistics"""
        if not GPU_AVAILABLE:
            return {"error": "GPU monitoring not available"}
        
        try:
            gpus = GPUtil.getGPUs()
            stats = []
            
            for gpu in gpus:
                stats.append({
                    "gpu_id": gpu.id,
                    "name": gpu.name,
                    "memory_used": f"{gpu.memoryUsed:.0f} MB",
                    "memory_total": f"{gpu.memoryTotal:.0f} MB",
                    "memory_util": f"{gpu.memoryUtil * 100:.1f}%",
                    "gpu_util": f"{gpu.load * 100:.1f}%",
                    "temperature": f"{gpu.temperature}°C"
                })
            
            result = {"gpus": stats}
            
            # Add CPU/Memory stats
            if PSUTIL_AVAILABLE:
                result["cpu"] = {
                    "cpu_percent": f"{psutil.cpu_percent()}%",
                    "memory_percent": f"{psutil.virtual_memory().percent}%",
                    "memory_used": f"{psutil.virtual_memory().used / (1024**3):.2f} GB"
                }
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_summary(self, minutes: int = None) -> Dict:
        """Get summary statistics"""
        with self.lock:
            samples = self.samples.copy()
        
        if not samples:
            return {"error": "No samples collected"}
        
        # Filter by time
        if minutes:
            cutoff_time = time.time() - (minutes * 60)
            samples = [s for s in samples if s["timestamp"] > cutoff_time]
        
        if not samples:
            return {"error": "No samples in time range"}
        
        # Separate GPU and CPU samples
        gpu_samples = [s for s in samples if "gpu_id" in s]
        cpu_samples = [s for s in samples if "cpu_percent" in s]
        
        summary = {}
        
        # GPU summary
        if gpu_samples:
            summary["gpu"] = {
                "avg_memory_util": round(sum(s["memory_util_percent"] for s in gpu_samples) / len(gpu_samples), 2),
                "max_memory_util": round(max(s["memory_util_percent"] for s in gpu_samples), 2),
                "avg_gpu_util": round(sum(s["gpu_util_percent"] for s in gpu_samples) / len(gpu_samples), 2),
                "max_gpu_util": round(max(s["gpu_util_percent"] for s in gpu_samples), 2),
                "avg_temperature": round(sum(s["temperature_c"] for s in gpu_samples) / len(gpu_samples), 2),
                "max_temperature": round(max(s["temperature_c"] for s in gpu_samples), 2),
                "samples_collected": len(gpu_samples)
            }
        
        # CPU summary
        if cpu_samples:
            summary["cpu"] = {
                "avg_cpu_percent": round(sum(s["cpu_percent"] for s in cpu_samples) / len(cpu_samples), 2),
                "max_cpu_percent": round(max(s["cpu_percent"] for s in cpu_samples), 2),
                "avg_memory_percent": round(sum(s["memory_percent"] for s in cpu_samples) / len(cpu_samples), 2),
                "max_memory_percent": round(max(s["memory_percent"] for s in cpu_samples), 2),
                "samples_collected": len(cpu_samples)
            }
        
        return summary
    
    def save_samples(self, filename: str = None):
        """Save all samples to file"""
        if filename is None:
            filename = f"gpu_samples_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.log_dir, filename)
        
        with self.lock:
            with open(filepath, 'w') as f:
                json.dump(self.samples, f, indent=2)
        
        print(f"💾 GPU samples saved: {filepath}")
        return filepath


# Decorator for automatic tracing
def trace_execution(agent_name: str, tracer: ExecutionTracer):
    """Decorator to automatically trace function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer.log_event(
                agent_name=agent_name,
                event_type="function_start",
                data={"function": func.__name__}
            )
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                tracer.log_event(
                    agent_name=agent_name,
                    event_type="function_end",
                    data={
                        "function": func.__name__,
                        "duration": duration,
                        "status": "success"
                    }
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                tracer.log_event(
                    agent_name=agent_name,
                    event_type="function_error",
                    data={
                        "function": func.__name__,
                        "duration": duration,
                        "error": str(e)
                    }
                )
                raise
        
        return wrapper
    return decorator


# Global instances (can be imported by other modules)
tracer = ExecutionTracer()
cost_tracker = CostTracker()
gpu_monitor = GPUMonitor()


if __name__ == "__main__":
    # Test the monitoring system
    print("Testing monitoring system...\n")
    
    # Test tracer
    trace_id = tracer.start_trace("Test task: Stack blocks")
    tracer.log_event("controller", "task_received", {"task": "stack blocks"})
    time.sleep(0.1)
    tracer.log_event("detector", "detection_complete", {"objects_found": 2})
    time.sleep(0.1)
    tracer.log_event("grasper", "grasp_computed", {"grasp_quality": 0.95})
    tracer.end_trace("completed")
    
    print("\n📊 Trace Summary:")
    print(json.dumps(tracer.get_trace_summary(trace_id), indent=2))
    
    # Test cost tracker
    cost_tracker.log_api_call("gpt-4o", 1000, 500, "controller", trace_id)
    cost_tracker.log_api_call("gpt-4o-mini", 500, 200, "detector", trace_id)
    
    print("\n💰 Cost Summary:")
    print(json.dumps(cost_tracker.get_summary(trace_id=trace_id), indent=2))
    
    # Test GPU monitor
    print("\n🖥️  Current GPU Stats:")
    print(json.dumps(gpu_monitor.get_current_stats(), indent=2))
    
    print("\n✅ Monitoring system test complete!")
