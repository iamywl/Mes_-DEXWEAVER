# DEXWEAVER MES Project

## Project Overview
- K8s 기반 클라우드 네이티브 MES (Manufacturing Execution System)
- 경북대학교 스마트 팩토리 프로젝트
- GS인증 표준 준수 (KISA 49, KS X 9003, ISO/IEC 25051)

## Tech Stack
- **Backend**: Python FastAPI (app.py, 46 endpoints, FN-001~038)
- **Frontend**: React 19 + Vite + Tailwind CSS 4 (single file: frontend/src/App.jsx, ~2851 lines)
- **DB**: PostgreSQL 15 (db/init.sql, 21 tables)
- **Infra**: Kubernetes v1.30+, Cilium eBPF, Jenkins CI/CD
- **Auth**: JWT (PyJWT + bcrypt)
- **AI**: Prophet, XGBoost, scikit-learn (IsolationForest), OR-Tools, SHAP
- **Deploy**: ConfigMap-based (no Docker build needed)

## Key Directories
```
MES_PROJECT/
├── app.py                 # FastAPI main router
├── api_modules/           # Backend business logic (28 modules)
├── frontend/src/App.jsx   # React SPA (14 menus)
├── db/init.sql            # DB schema + seed data
├── infra/                 # K8s manifests (7 YAML files)
├── doc/                   # Development docs (ARCH, HANDOVER, etc.)
├── research/              # Market research (separate from dev docs)
│   ├── 01~04              # Part 1: Basic research
│   ├── 05~07              # Part 2: Feature deep-dive
│   ├── 08~11              # Part 3: Business frameworks
│   └── limitations/       # Limitations analysis
├── init.sh                # One-click startup script
└── env.sh                 # Environment variables
```

## Coding Standards
- **Python**: PEP 8, type hints, Google-style docstrings, snake_case
- **JavaScript**: ESLint, 2-space indent, camelCase, JSDoc
- **Git**: Conventional commits, Korean descriptions OK

## Key API Modules
| Module | Functions | Description |
|--------|-----------|-------------|
| mes_auth | FN-001~003 | JWT login/register/permissions |
| mes_items | FN-004~007 | Item CRUD with pagination |
| mes_bom | FN-008~009 | BOM explode/where-used |
| mes_process | FN-010~012 | Process & routing management |
| mes_equipment | FN-013~014, FN-032~034 | Equipment + AI failure prediction |
| mes_plan | FN-015~017 | Production plans + schedule optimization |
| mes_work | FN-020~024 | Work orders & results |
| mes_quality | FN-025~027 | Quality inspection & defects |
| mes_inventory | FN-029~031 | Inventory in/out/move/trace |
| mes_reports | FN-035~037 | Reports + AI insights |
| mes_ai_prediction | FN-018 | Demand forecasting (Prophet) |
| mes_defect_predict | FN-028 | Defect prediction (XGBoost) |

## DB Schema (21 tables)
users, user_permissions, items, bom, processes, equipments, routings,
equip_status_log, production_plans, work_orders, work_results,
quality_standards, inspections, inspection_details, defect_codes,
inventory, inventory_transactions, shipments, defect_history,
equip_sensors, ai_forecasts

## Important Notes
- Research docs (research/) must remain separate from dev docs (doc/)
- Frontend is a single-file SPA (App.jsx) - consider modularization
- AI modules have graceful fallbacks when libraries unavailable
- All API endpoints require JWT auth except /api/health and /api/auth/login
