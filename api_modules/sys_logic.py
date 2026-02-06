import os, subprocess, json
from kubernetes import client, config

def get_pods(): # /api/k8s/pods 대응
    try:
        config.load_incluster_config()
        return [{"name": p.metadata.name, "status": p.status.phase} for p in client.CoreV1Api().list_namespaced_pod(namespace="default").items]
    except: return []

def get_flows(): # /api/network/flows 대응
    try:
        res = subprocess.check_output("hubble observe --server hubble-relay.kube-system.svc.cluster.local:80 -o json --last 5", shell=True, timeout=1).decode('utf-8')
        return [json.loads(l) for l in res.strip().split('\n') if l]
    except: return []

def get_infra(): # /api/infra/status 대응
    load = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0.5
    return {"cpu": f"{load*20:.1f}%", "mem": "54%"}
