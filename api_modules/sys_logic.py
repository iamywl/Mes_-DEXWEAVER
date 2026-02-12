"""System infrastructure metrics and Kubernetes pod status."""

import os

import psutil
from kubernetes import client, config


def get_pods():
    """Return list of pods in the default namespace."""
    try:
        config.load_incluster_config()
        pods = client.CoreV1Api().list_namespaced_pod(namespace="default")
        return [
            {"name": p.metadata.name, "status": p.status.phase}
            for p in pods.items
        ]
    except Exception:
        return []


async def get_infra():
    """Collect system CPU and memory metrics using psutil.

    Returns dict with both numeric values (cpu_load, memory_usage) and
    formatted strings (cpu, mem) for frontend/client compatibility.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        vmem = psutil.virtual_memory()
        mem_percent = vmem.percent
        return {
            "cpu_load": float(cpu_percent),
            "memory_usage": float(mem_percent),
            "cpu": f"{cpu_percent:.1f}%",
            "mem": f"{mem_percent:.1f}%",
        }
    except Exception:
        try:
            load = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.5
            cpu_pct = min(load * 20, 100.0)
            return {
                "cpu_load": cpu_pct,
                "memory_usage": 0.0,
                "cpu": f"{cpu_pct:.1f}%",
                "mem": "0%",
            }
        except Exception:
            return {
                "cpu_load": 0.0,
                "memory_usage": 0.0,
                "cpu": "0%",
                "mem": "0%",
            }
