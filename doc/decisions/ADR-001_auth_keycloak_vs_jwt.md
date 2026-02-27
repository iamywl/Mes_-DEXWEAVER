# ADR-001: 인증 방식 선택 — Keycloak OIDC/PKCE vs JWT 커스텀

| 항목 | 내용 |
|------|------|
| **상태** | 검토 중 (Under Review) |
| **작성일** | 2026-02-27T17:30:00 KST |
| **작성자** | 개발팀 |
| **영향 범위** | 백엔드 인증 모듈, 프론트엔드 로그인, K8s 인프라 |

---

## 1. 현황

현재 프로젝트는 **두 가지 인증 체계가 혼재**되어 있다.

| 구분 | 현재 상태 |
|------|-----------|
| 백엔드 코드 (`mes_auth.py`) | **JWT 커스텀** — PyJWT + bcrypt 직접 구현 |
| 프론트엔드 (`package.json`) | `keycloak-js` 패키지 설치됨 (미사용) |
| K8s 매니페스트 (`infra/keycloak.yaml`) | Keycloak 배포 YAML 존재 |
| 초기화 스크립트 (`setup-keycloak.sh`) | Realm/Client 자동 설정 스크립트 존재 |
| README.md | ~~Keycloak OIDC/PKCE~~ → JWT로 수정 완료 (2026-02-27) |

**문제**: 코드는 JWT 커스텀인데, 인프라에 Keycloak 잔재가 남아있어 혼란을 유발한다.

---

## 2. 선택지 비교

### Option A: JWT 커스텀 유지 (현재 방식)

```
Client → POST /api/auth/login → mes_auth.py → bcrypt 검증 → JWT 발급 → Client
```

**장점**
- 외부 의존성 없음 (Keycloak 서버 불필요)
- 구현이 단순하고 디버깅 쉬움
- 리소스 부담 최소 (별도 Java 서버 불필요)
- 학과 프로젝트/데모 환경에 적합

**단점**
- SSO, MFA, 소셜 로그인 직접 구현 필요
- 토큰 갱신(refresh), 토큰 폐기(revoke) 로직 부재
- 보안 취약점 발견 시 직접 패치해야 함
- 감사 로그(audit log) 미구현
- 세션 관리 기능 없음 (동시 로그인 제어 불가)

**잔여 작업**: Keycloak 관련 잔재 정리 필요
- `infra/keycloak.yaml` 삭제 또는 주석 처리
- `setup-keycloak.sh` 삭제
- `frontend/package.json`에서 `keycloak-js` 제거
- README에서 Keycloak 관련 서술 정리

---

### Option B: Keycloak OIDC/PKCE 전환

```
Client → Keycloak Login Page → OIDC Authorization Code + PKCE
  → Keycloak → ID Token + Access Token 발급
  → Client → Authorization: Bearer <token> → FastAPI → Token 검증 (Keycloak 공개키)
```

**장점**
- SSO 기본 내장 (여러 서비스 단일 로그인)
- MFA(TOTP, WebAuthn), 소셜 로그인(Google, GitHub) 내장
- OIDC/OAuth2 국제 표준 준수 → GS인증 보안 항목 강화
- Keycloak 관리 콘솔에서 사용자/역할/클라이언트 관리
- 감사 로그, 브루트포스 방어, 세션 관리 기본 제공
- 보안 패치를 Keycloak 커뮤니티가 담당

**단점**
- Keycloak 서버 별도 운영 필요 (Java 기반, 메모리 512MB~1GB)
- 초기 설정 복잡도 증가 (Realm, Client, Role 매핑)
- 개발 환경에서 Keycloak 의존성으로 단독 테스트 어려움
- 장애 포인트 추가 (Keycloak 다운 시 전체 인증 불가)

**필요 작업**
- `mes_auth.py` 전면 교체: JWT 자체 발급 → Keycloak 토큰 검증으로 전환
- FastAPI 미들웨어: `python-keycloak` 또는 `authlib` 라이브러리 연동
- 프론트엔드: `keycloak-js`로 로그인 플로우 교체
- DB `users` 테이블: Keycloak에 사용자 마이그레이션
- K8s: Keycloak Pod 상시 기동, PV 연결 (설정 영속화)

---

## 3. 의사결정 매트릭스

| 평가 기준 | 가중치 | JWT 커스텀 | Keycloak OIDC |
|-----------|--------|-----------|---------------|
| 보안 수준 | 30% | 6/10 | 9/10 |
| 운영 단순성 | 20% | 9/10 | 5/10 |
| 확장성 (SSO/MFA) | 20% | 3/10 | 10/10 |
| 리소스 효율 | 15% | 10/10 | 5/10 |
| GS인증 대응 | 15% | 7/10 | 9/10 |
| **가중 합계** | **100%** | **6.65** | **7.85** |

---

## 4. 권고안

| 단계 | 권고 |
|------|------|
| **현재 (학과 프로젝트)** | **JWT 커스텀 유지** — Keycloak 잔재만 정리하여 혼란 제거 |
| **실서비스 전환 시** | **Keycloak OIDC/PKCE 전환** — 보안·확장성·인증 표준 준수에 유리 |

---

## 5. TODO (미결 사항)

- [ ] Keycloak 잔재 정리 여부 결정 (삭제 vs 주석 처리)
- [ ] JWT refresh token 로직 추가 여부
- [ ] 실서비스 전환 시점 Keycloak 연동 계획 수립
