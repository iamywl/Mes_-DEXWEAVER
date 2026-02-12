import os, subprocess, json
from kubernetes import client, config
import psutil

def get_pods():
    try:
        config.load_incluster_config()
        return [{"name": p.metadata.name, "status": p.status.phase} for p in client.CoreV1Api().list_namespaced_pod(namespace="default").items]
    except: return []

def get_flows():
    try:
        res = subprocess.check_output("hubble observe --server hubble-relay.kube-system.svc.cluster.local:80 -o json --last 5", shell=True, timeout=1).decode('utf-8')
        return [json.loads(l) for l in res.strip().split('\n') if l]
    except: return []

def get_infra():
    """Collect system CPU and memory metrics using psutil.
    
    Returns dict with both numeric values (cpu_load, memory_usage) and
    formatted strings (cpu, mem) for frontend/client compatibility.
    In Kubernetes pod, returns pod-level resource utilization.
    """
    try:
        # CPU: percent usage (0-100) across all cores, non-blocking
        cpu_percent = psutil.cpu_percent(interval=0.1)
        # Memory: virtual memory info
        vmem = psutil.virtual_memory()
        mem_percent = vmem.percent
        return {
            "cpu_load": float(cpu_percent),
            "memory_usage": float(mem_percent),
            "cpu": f"{cpu_percent:.1f}%",
            "mem": f"{mem_percent:.1f}%"
        }
    except Exception:
        # Fallback if psutil fails
        try:
            load = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0.5
            cpu_pct = min(load * 20, 100.0)
            return {
                "cpu_load": cpu_pct,
                "memory_usage": 0.0,
                "cpu": f"{cpu_pct:.1f}%",
                "mem": "0%"
            }
        except Exception:
            return {
                "cpu_load": 0.0,
                "memory_usage": 0.0,
                "cpu": "0%",
                "mem": "0%"
            }
