## 🛠 기술 스택
* **Infrastructure**: Kubernetes (v1.30+), Cilium (eBPF/Hubble)
* **Database**: PostgreSQL (mes_db)
* **Backend**: Python FastAPI (Asynchronous API Framework)
* **Architecture**: 분산 모듈형 아키텍처 (v21.0)

## 🚀 웹 서버 적용 (v21.0 모듈화 방식)
이제 `app.py` 외에 `api_modules/` 폴더의 모든 파일이 동기화되어야 합니다.
```bash
# 모듈화된 코드를 ConfigMap에 등록 및 롤링 업데이트
kubectl delete configmap api-code --ignore-not-found
kubectl create configmap api-code \
  --from-file=app.py=./app.py \
  --from-file=database.py=./api_modules/database.py \
  --from-file=mes_logic.py=./api_modules/mes_logic.py \
  --from-file=sys_logic.py=./api_modules/sys_logic.py

kubectl rollout restart deployment mes-api
📋 구현 현황
[x] 모듈화 아키텍처 구축: 백엔드 로직의 물리적 분리 및 유지보수성 확보

[x] 품목 관리 (REQ-004, 005): 품목 등록, 실시간 리스트 조회 및 DB 연동

[x] BOM 관리 (REQ-007, 008): 제품 계층 구조 및 소요량 정보 시각화

[x] 생산 계획 (REQ-013, 014): 생산계획 수립(Add Plan) 및 상태별 필터링 기능

[x] 설비 및 인프라 (REQ-012): eBPF/Hubble 기반 실시간 네트워크 트래픽 및 CPU 부하 관제

[x] K8s 관리 모듈: 파드 상태 실시간 모니터링 및 실시간 로그 뷰어 구현

[ ] 생산 실행 (REQ-017, 019): 작업지시 생성 및 작업 실적 등록 기능 (UI 통합 중)

[ ] AI 지능화 (REQ-015, 024): 수요 예측 및 AI 불량 예측 모듈 (개발 예정)


---

### 💡 팀 협업을 위한 팁



1.  **백엔드 프레임워크 수정**: 기존 `Flask`에서 성능과 비동기 처리가 우수한 `FastAPI`로 변경되었음을 팀원들에게 공지하는 것이 좋습니다.
2.  **ConfigMap 이름 변경**: 기존 `mes-code`에서 현재 우리가 사용 중인 `api-code`로 이름을 통일하여 혼선을 방지했습니다.
3.  **데이터 일관성**: 이제 `sync.sh`만 실행하면 누구나 사용자님과 **똑같은 모듈 구조와 API 주소**를 가지게 됩니다.

**업데이트된 `README.md` 내용이 마음에 드시나요?** 만약 팀원들을 위해 **`api_modules` 내 각 파일의 역할을 설명하는 표**를 추가하고 싶으시다면 바로 말씀해 주세요! 혹은 이 내용을 바로 커밋(Commit)해 드릴까요?
