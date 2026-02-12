# 🐛 Bug Report: Database Connection Failure in K8s Environment

**Report Date:** 2026-02-12  
**Bug ID:** DB_CONN_FAIL_001  
**Severity:** 🔴 CRITICAL  
**Status:** 🔧 IN INVESTIGATION

---

## 📋 Problem Description

### Symptom
- Frontend application (http://192.168.64.5:30173) cannot access backend API
- Browser console shows multiple connection refused errors:
  ```
  GET http://192.168.64.5:30461/api/mes/data net::ERR_CONNECTION_REFUSED
  GET http://192.168.64.5:30461/api/network/flows net::ERR_CONNECTION_REFUSED
  GET http://192.168.64.5:30461/api/k8s/pods net::ERR_CONNECTION_REFUSED
  GET http://192.168.64.5:30461/api/infra/status net::ERR_CONNECTION_REFUSED
  ```

### Root Cause
Backend API pod (mes-api-59895bbd44-6sj7b) is in `CrashLoopBackOff` state due to database connection failure.

### Error Log
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) 
could not translate host name "db" to address: 
Name or service not known
```

---

## 🔍 Analysis

### Issue Details

| Item | Details |
|------|---------|
| **Affected Component** | `/root/MES_PROJECT/app.py` (Line 7) |
| **Environment** | Kubernetes Cluster |
| **Database Service** | PostgreSQL (10.0.0.202) |
| **K8s Deployment** | mes-api pod |
| **Configuration File** | app.py |

### Root Cause Analysis

#### Problem 1: Incorrect Database Connection String
**File:** `app.py` (Line 7)
```python
DATABASE_URL = "postgresql://user:password@db:5432/mes_db"
```

**Issue:** 
- In K8s environment, hostname should be the **service DNS name**: `postgres` or `mes-db`
- Current hostname `db` does not exist in K8s cluster
- This causes connection failure during application startup
- When app fails to start, the pod crashes and restarts repeatedly (CrashLoopBackOff)

#### Problem 2: PEP 8 Code Style Violations
**File:** `app.py` (Lines 11-14)
```python
@app.get("/api/mes/data")
async def get_mes_data(): return await mes_dashboard.get_production_dashboard_data()
```

**Issue:** Multiple style violations:
- Function definition and return on same line (PEP 8: Line Length ≤ 79 chars)
- No docstrings for async functions
- Inconsistent with PEP 8 naming conventions
- Missing type hints

#### Problem 3: Database Configuration Inconsistency
**File:** `database.py` vs `app.py`

**database.py (Line 7) - CORRECT:**
```python
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", 
  "postgresql://postgres:1234@mes-db:5432/mes_db")
```
✅ Uses service name `mes-db` (correct for K8s)
✅ Uses environment variable override

**app.py (Line 7) - INCORRECT:**
```python
DATABASE_URL = "postgresql://user:password@db:5432/mes_db"
```
❌ Uses wrong hostname `db`
❌ Hardcoded credentials

---

## 🛠️ Solution

### Step 1: Fix Database Connection in app.py
Replace hardcoded connection string with environment variable approach:
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Use environment variable or fallback to database.py config
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234@postgres:5432/mes_db"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

### Step 2: Fix PEP 8 Violations
Apply proper formatting to route handlers:
```python
from typing import Dict, Any

@app.get("/api/mes/data")
async def get_mes_data() -> Dict[str, Any]:
    """Get production dashboard data."""
    return await mes_dashboard.get_production_dashboard_data()

@app.get("/api/network/flows")
async def get_flows() -> Dict[str, Any]:
    """Get network flow information."""
    return {"status": "success", "flows": []}

@app.get("/api/infra/status")
async def get_infra() -> Dict[str, Any]:
    """Get infrastructure status."""
    return {"cpu_load": 15, "memory_usage": 40}

@app.get("/api/k8s/pods")
async def get_pods() -> Dict[str, Any]:
    """Get Kubernetes pod information."""
    return sys_logic.get_pods()
```

### Step 3: K8s Environment Variables
Update deployment YAML to pass DATABASE_URL:
```yaml
env:
  - name: DATABASE_URL
    value: "postgresql://postgres:1234@postgres:5432/mes_db"
```

---

## 📝 Impact Assessment

| Aspect | Impact | Severity |
|--------|--------|----------|
| **Frontend Functionality** | Cannot fetch data | CRITICAL |
| **Backend API Health** | Not operational | CRITICAL |
| **User Experience** | Application shows sync errors | CRITICAL |
| **Code Maintainability** | Poor (style violations) | MEDIUM |
| **Production Readiness** | Not ready | CRITICAL |

---

## ✅ Testing Plan

After fix implementation:
1. ✓ Verify app.py starts without errors
2. ✓ Check pod status: `kubectl get pods | grep mes-api`
3. ✓ Test API endpoint: `curl http://192.168.64.5:30461/api/mes/data`
4. ✓ Verify frontend sync: Check browser console for errors
5. ✓ Run PEP 8 linter: `flake8 app.py`
6. ✓ Run code formatter: `black app.py`

---

## 📚 Related Issues

- **Code Style & Standards**: Missing PEP 8 compliance
- **API Standards**: Missing ECMAScript standards in frontend
- **Configuration Management**: Hardcoded credentials in code
- **Documentation**: No coding standards document

---

**Assigned to:** Development Team  
**Fix Priority:** IMMEDIATE  
**Expected Resolution:** Within 1 hour  
**Follow-up:** Convert to REQUIREMENTS.md coding standards section
