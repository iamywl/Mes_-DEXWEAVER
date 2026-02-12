# Bug Report: Frontend `net::ERR_CONNECTION_REFUSED` to Backend API

## Problem Description
The frontend application was consistently failing to connect to the backend API services, manifesting as `net::ERR_CONNECTION_REFUSED` errors in the browser console. These errors were observed for various API endpoints, including `/api/mes/data`, `/api/network/flows`, `/api/infra/status`, and `/api/k8s/pods`. The console logs indicated connection attempts to `http://192.168.64.5:30461/api/...`.

## Root Cause Analysis

1.  **Backend Service Exposure:** The `k8s/backend-service.yaml` file defined the backend service with `type: ClusterIP`. A `ClusterIP` service is designed for internal communication within the Kubernetes cluster and is not directly accessible from outside the cluster. This prevented the frontend (which is externally accessed) from reaching the backend.

2.  **Frontend API URL Configuration:** The `frontend/src/api.js` file configured the `API_URL` to `http://localhost:8000`. When the frontend application, running within its own pod, attempted to connect to `localhost:8000`, it was trying to establish a connection to itself, not to the separate backend service. This misconfiguration meant the frontend was unable to locate and communicate with the backend.

3.  **Discrepancy in Connection Attempts:** The browser console logs showed connection attempts to `http://192.168.64.5:30461/api/...`, which differed from the `localhost:8000` configured in `api.js`. This suggested a potential caching issue, an outdated frontend image, or an underlying network configuration (like a proxy) attempting to route to a specific NodePort (`30461` is a common NodePort range) that was not correctly exposed for the backend. However, the fundamental issue remained the backend's lack of external exposure and the frontend's incorrect target URL.

## Solution Implemented

1.  **Backend Service Type Change:**
    *   **File:** `/root/MES_PROJECT/k8s/backend-service.yaml`
    *   **Change:** Modified the service `type` from `ClusterIP` to `NodePort` and explicitly set a `nodePort` to `30461`. This exposes the backend service externally on the Minikube node's IP address at the specified port, allowing the frontend to reach it.

    ```yaml
    # Before
    apiVersion: v1
    kind: Service
    metadata:
      name: backend-service
    spec:
      selector:
        app: backend
      ports:
        - protocol: TCP
          port: 8000
          targetPort: 8000
      type: ClusterIP
    ```

    ```yaml
    # After
    apiVersion: v1
    kind: Service
    metadata:
      name: backend-service
    spec:
      selector:
        app: backend
      ports:
        - protocol: TCP
          port: 8000
          targetPort: 8000
          nodePort: 30461 # Added
      type: NodePort # Changed
    ```

2.  **Frontend API URL Update:**
    *   **File:** `/root/MES_PROJECT/frontend/src/api.js`
    *   **Change:** Updated the `API_URL` constant to point to the Minikube IP address (`192.168.64.5`) and the newly exposed backend `nodePort` (`30461`), including the `/api` prefix that the backend uses.

    ```javascript
    // Before
    const API_URL = 'http://localhost:8000'; // Adjust as per your FastAPI service URL
    ```

    ```javascript
    // After
    const API_URL = 'http://192.168.64.5:30461/api';
    ```

These changes ensure that the backend service is externally accessible via a known NodePort and that the frontend is configured to correctly target this external endpoint for its API requests, resolving the connection refused errors.
