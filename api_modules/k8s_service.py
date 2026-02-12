"""Kubernetes API wrapper for pod status, logs, and Hubble network flows."""

import json
import subprocess

from kubernetes import client, config


def get_status():
    """Return pod status list from default namespace."""
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(namespace="default")
        return [
            {"name": p.metadata.name, "status": p.status.phase}
            for p in pods.items
        ]
    except Exception:
        return []


def get_logs(name):
    """Return last 50 lines of logs for a given pod."""
    try:
        config.load_incluster_config()
        return client.CoreV1Api().read_namespaced_pod_log(
            name=name, namespace="default", tail_lines=50
        )
    except Exception:
        return "Logs Unavailable"


def get_flows():
    """Fetch recent network flows from Hubble relay."""
    try:
        cmd = (
            "hubble observe"
            " --server hubble-relay.kube-system.svc.cluster.local:80"
            " -o json --last 5"
        )
        res = subprocess.check_output(
            cmd, shell=True, timeout=1
        ).decode("utf-8")
        return [json.loads(line) for line in res.strip().split("\n") if line]
    except Exception:
        return []
