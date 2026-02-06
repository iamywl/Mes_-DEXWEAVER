from kubernetes import client, config
import os, subprocess, json

def get_status():
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(namespace="default")
        return [{"name": p.metadata.name, "status": p.status.phase} for p in pods.items]
    except: return []

def get_logs(name):
    try:
        config.load_incluster_config()
        return client.CoreV1Api().read_namespaced_pod_log(name=name, namespace="default", tail_lines=50)
    except: return "Logs Unavailable"

def get_flows():
    try:
        res = subprocess.check_output("hubble observe --server hubble-relay.kube-system.svc.cluster.local:80 -o json --last 5", shell=True, timeout=1).decode('utf-8')
        return [json.loads(l) for l in res.strip().split('\n') if l]
    except: return []
