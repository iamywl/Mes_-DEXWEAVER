"""Kubernetes API wrapper for pod status, logs, and Hubble network flows."""

import json
import hashlib
import random
import subprocess
import time
from datetime import datetime, timedelta, timezone

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


# ── Hubble-style rich flow & service map data ──────────────

_MES_SERVICES = [
    {"name": "mes-frontend", "namespace": "default", "type": "Deployment",
     "protocol": "HTTP", "port": 80, "ip": "10.244.0.11"},
    {"name": "mes-api-service", "namespace": "default", "type": "Deployment",
     "protocol": "HTTP", "port": 80, "ip": "10.244.0.12"},
    {"name": "postgres", "namespace": "default", "type": "StatefulSet",
     "protocol": "TCP", "port": 5432, "ip": "10.244.0.13"},
    {"name": "kube-dns", "namespace": "kube-system", "type": "Deployment",
     "protocol": "UDP", "port": 53, "ip": "10.96.0.10"},
    {"name": "hubble-relay", "namespace": "kube-system", "type": "Deployment",
     "protocol": "gRPC", "port": 4245, "ip": "10.244.0.20"},
    {"name": "cilium-agent", "namespace": "kube-system", "type": "DaemonSet",
     "protocol": "TCP", "port": 4240, "ip": "10.244.0.21"},
]

_FLOW_TEMPLATES = [
    # frontend → api (HTTP)
    {"src": "mes-frontend", "dst": "mes-api-service", "proto": "HTTP",
     "port": 80, "l7_type": "GET /api/mes/data", "verdict": "FORWARDED"},
    {"src": "mes-frontend", "dst": "mes-api-service", "proto": "HTTP",
     "port": 80, "l7_type": "GET /api/network/flows", "verdict": "FORWARDED"},
    {"src": "mes-frontend", "dst": "mes-api-service", "proto": "HTTP",
     "port": 80, "l7_type": "GET /api/infra/status", "verdict": "FORWARDED"},
    {"src": "mes-frontend", "dst": "mes-api-service", "proto": "HTTP",
     "port": 80, "l7_type": "GET /api/k8s/pods", "verdict": "FORWARDED"},
    {"src": "mes-frontend", "dst": "mes-api-service", "proto": "HTTP",
     "port": 80, "l7_type": "GET /api/items", "verdict": "FORWARDED"},
    {"src": "mes-frontend", "dst": "mes-api-service", "proto": "HTTP",
     "port": 80, "l7_type": "POST /api/auth/login", "verdict": "FORWARDED"},
    # api → postgres (TCP)
    {"src": "mes-api-service", "dst": "postgres", "proto": "TCP",
     "port": 5432, "l7_type": "PostgreSQL query", "verdict": "FORWARDED"},
    {"src": "mes-api-service", "dst": "postgres", "proto": "TCP",
     "port": 5432, "l7_type": "PostgreSQL query", "verdict": "FORWARDED"},
    {"src": "mes-api-service", "dst": "postgres", "proto": "TCP",
     "port": 5432, "l7_type": "PostgreSQL query", "verdict": "FORWARDED"},
    # DNS queries
    {"src": "mes-frontend", "dst": "kube-dns", "proto": "UDP",
     "port": 53, "l7_type": "DNS A mes-api-service.default", "verdict": "FORWARDED"},
    {"src": "mes-api-service", "dst": "kube-dns", "proto": "UDP",
     "port": 53, "l7_type": "DNS A postgres.default", "verdict": "FORWARDED"},
    # api → hubble-relay (gRPC)
    {"src": "mes-api-service", "dst": "hubble-relay", "proto": "TCP",
     "port": 4245, "l7_type": "gRPC hubble.observe", "verdict": "FORWARDED"},
    # health checks (from external)
    {"src": "world", "dst": "mes-frontend", "proto": "TCP",
     "port": 30173, "l7_type": "NodePort ingress", "verdict": "FORWARDED"},
    {"src": "world", "dst": "mes-api-service", "proto": "TCP",
     "port": 30461, "l7_type": "NodePort ingress", "verdict": "FORWARDED"},
    # dropped traffic (occasional)
    {"src": "world", "dst": "postgres", "proto": "TCP",
     "port": 5432, "l7_type": "External access attempt", "verdict": "DROPPED"},
    {"src": "world", "dst": "cilium-agent", "proto": "TCP",
     "port": 4240, "l7_type": "Unauthorized access", "verdict": "DROPPED"},
]

_svc_lookup = {s["name"]: s for s in _MES_SERVICES}


def _make_flow(template, ts):
    """Build a single Hubble-style flow event from a template."""
    src_svc = _svc_lookup.get(template["src"])
    dst_svc = _svc_lookup.get(template["dst"])
    src_ns = src_svc["namespace"] if src_svc else "external"
    dst_ns = dst_svc["namespace"] if dst_svc else "external"
    src_ip = src_svc["ip"] if src_svc else f"192.168.1.{random.randint(100,200)}"
    dst_ip = dst_svc["ip"] if dst_svc else f"10.244.0.{random.randint(30,50)}"
    src_port = random.randint(32000, 65000)

    flow_id = hashlib.md5(
        f"{ts}{template['src']}{template['dst']}{random.random()}".encode()
    ).hexdigest()[:16]

    return {
        "flow_id": flow_id,
        "time": ts.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "timestamp": ts.isoformat(),
        "verdict": template["verdict"],
        "drop_reason": "POLICY_DENIED" if template["verdict"] == "DROPPED" else "",
        "ethernet": {"source": f"0a:58:0a:f4:00:{random.randint(10,99):02x}",
                      "destination": f"0a:58:0a:f4:00:{random.randint(10,99):02x}"},
        "IP": {"source": src_ip, "destination": dst_ip},
        "l4": {"protocol": template["proto"],
               "source_port": src_port,
               "destination_port": template["port"]},
        "l7": {"type": template["l7_type"]},
        "source": {
            "identity": random.randint(1000, 9999),
            "namespace": src_ns,
            "pod_name": template["src"] + (f"-{random.choice('abcdef')}{random.randint(1,9)}" if src_svc else ""),
            "labels": [f"app={template['src']}", f"k8s:ns={src_ns}"],
        },
        "destination": {
            "identity": random.randint(1000, 9999),
            "namespace": dst_ns,
            "pod_name": template["dst"] + (f"-{random.choice('abcdef')}{random.randint(1,9)}" if dst_svc else ""),
            "labels": [f"app={template['dst']}", f"k8s:ns={dst_ns}"],
        },
        "traffic_direction": "INGRESS" if not src_svc else "EGRESS",
        "trace_observation_point": "TO_ENDPOINT",
        "is_reply": False,
    }


def get_hubble_flows(last_n=50):
    """Return rich Hubble-style flow events.

    Attempts real Hubble relay first, falls back to simulated data.
    """
    try:
        cmd = (
            "hubble observe"
            " --server hubble-relay.kube-system.svc.cluster.local:80"
            " -o json --last 50"
        )
        res = subprocess.check_output(cmd, shell=True, timeout=2).decode()
        flows = [json.loads(line) for line in res.strip().split("\n") if line]
        if flows:
            return flows
    except Exception:
        pass

    # Generate simulated flows
    now = datetime.now(timezone.utc)
    seed = int(now.timestamp()) // 5
    rng = random.Random(seed)
    flows = []
    for i in range(last_n):
        t_offset = rng.uniform(0, 30)
        ts = now - timedelta(seconds=t_offset)
        tmpl = rng.choice(_FLOW_TEMPLATES)
        flows.append(_make_flow(tmpl, ts))
    flows.sort(key=lambda f: f["time"], reverse=True)
    return flows


def get_service_map():
    """Build a Hubble-style service dependency map from flow data."""
    flows = get_hubble_flows(100)

    services = {}
    connections = {}

    for f in flows:
        src_name = f.get("source", {}).get("pod_name", "").rsplit("-", 1)[0]
        dst_name = f.get("destination", {}).get("pod_name", "").rsplit("-", 1)[0]
        src_ns = f.get("source", {}).get("namespace", "unknown")
        dst_ns = f.get("destination", {}).get("namespace", "unknown")
        verdict = f.get("verdict", "FORWARDED")
        proto = f.get("l4", {}).get("protocol", "TCP")
        dst_port = f.get("l4", {}).get("destination_port", 0)

        if src_name and src_name not in services:
            svc = _svc_lookup.get(src_name, {})
            services[src_name] = {
                "id": src_name, "name": src_name,
                "namespace": src_ns,
                "type": svc.get("type", "Pod"),
                "protocol": svc.get("protocol", "TCP"),
                "port": svc.get("port", 0),
                "ip": f.get("IP", {}).get("source", ""),
                "traffic_in": 0, "traffic_out": 0,
                "forwarded": 0, "dropped": 0,
            }
        if dst_name and dst_name not in services:
            svc = _svc_lookup.get(dst_name, {})
            services[dst_name] = {
                "id": dst_name, "name": dst_name,
                "namespace": dst_ns,
                "type": svc.get("type", "Pod"),
                "protocol": svc.get("protocol", "TCP"),
                "port": svc.get("port", 0),
                "ip": f.get("IP", {}).get("destination", ""),
                "traffic_in": 0, "traffic_out": 0,
                "forwarded": 0, "dropped": 0,
            }

        if src_name in services:
            services[src_name]["traffic_out"] += 1
            if verdict == "FORWARDED":
                services[src_name]["forwarded"] += 1
            else:
                services[src_name]["dropped"] += 1

        if dst_name in services:
            services[dst_name]["traffic_in"] += 1
            if verdict == "FORWARDED":
                services[dst_name]["forwarded"] += 1
            else:
                services[dst_name]["dropped"] += 1

        key = f"{src_name}→{dst_name}"
        if key not in connections:
            connections[key] = {
                "id": key, "source": src_name, "target": dst_name,
                "protocol": proto, "port": dst_port,
                "forwarded_count": 0, "dropped_count": 0,
                "last_seen": f.get("time", ""),
                "l7_types": set(),
            }
        if verdict == "FORWARDED":
            connections[key]["forwarded_count"] += 1
        else:
            connections[key]["dropped_count"] += 1
        l7 = f.get("l7", {}).get("type", "")
        if l7:
            connections[key]["l7_types"].add(l7)

    # Serialize sets
    for c in connections.values():
        c["l7_types"] = list(c["l7_types"])[:5]
        c["total_count"] = c["forwarded_count"] + c["dropped_count"]

    return {
        "services": list(services.values()),
        "connections": list(connections.values()),
    }
