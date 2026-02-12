# 🏭 스마트 팩토리 MES 프로젝트 요구사항 정의서

본 문서는 경북대학교 실습 환경(K8s)을 기반으로 구축되는 싱글 테넌트 MES 시스템의 요구사항을 정의합니다.

## 1. 프로젝트 개요
* **프로젝트명**: K8s 기반 스마트 팩토리 MES (Kyungpook National Univ.)
* **인프라**: Kubernetes (v1.30+), Cilium (eBPF 기반 네트워크)
* **데이터베이스**: PostgreSQL
* **백엔드/프론트엔드**: Python Flask (API Only) & React (Frontend)

## 2. 시스템 아키텍처 (Infrastructure)
* **Containerization**: 모든 서비스는 Docker 컨테이너로 추상화됨.
* **Orchestration**: Kubernetes를 통한 서비스 배포 및 자동 복구(Self-healing).
* **Storage**: ConfigMap을 활용한 소스 코드 동기화 및 DB 연동.

## 3. 기능 요구사항 (Functional Requirements)

### [REQ-001] 데이터베이스 기초 환경 구축
- [x] PostgreSQL 컨테이너 배포 및 `mes_db` 데이터베이스 생성.
- [x] 서비스 재시작 시에도 테이블 스키마 자동 빌드 스크립트 구현.

### [REQ-004] 품목 관리 (Item Management)
- [x] 품목(원자재, 반제품, 완제품) 코드 및 정보 등록.
- [x] 웹 화면을 통한 실시간 품목 리스트 조회.

### [REQ-007] BOM(Bill of Materials) 관리
- [ ] 제품 구성 정보(레시피) 등록 기능.
- [ ] 상위 품목과 하위 품목 간의 조립 관계 설정.

### [REQ-010] 생산 및 설비 모니터링
- [x] 생산 계획(Production Plans) 현황 대시보드 출력.
- [x] 설비(Equipments) 상태(RUN/IDLE) 실시간 모니터링 화면.

## 4. 기술 요구사항 (Technical Requirements)
* **보안**: 컨테이너 간 격리 및 네트워크 정책 적용 고려.
* **자동화**: `start_mes.sh`를 통한 시스템 부팅 및 환경 설정 자동화.
* **버전 관리**: GitHub(`seohannyeong/MES_PROJECT`)를 통한 SSH 기반 협업 및 코드 관리.
* **코딩 표준**: PEP 8 (Python) 및 ECMAScript (JavaScript) 준수 필수.

## 5. 데이터베이스 스키마 설계
| 테이블명 | 용도 | 비고 |
| :--- | :--- | :--- |
| **items** | 품목 마스터 정보 | PK: item_code |
| **production_plans** | 생산 계획 및 상태 | FK: item_code |
| **processes** | 생산 공정 정의 | - |
| **equipments** | 공장 설비 현황 | - |

## 6. 코딩 표준 및 컨벤션 (Coding Standards)

### Python (Backend) - PEP 8 준수

#### 6.1 기본 규칙
- **라인 길이**: 최대 79자 (코드), 최대 99자 (문서)
- **들여쓰기**: 4 스페이스 (탭 사용 금지)
- **빈 라인**: 함수/클래스 간 2줄, 메서드 간 1줄
- **임포트**: 표준 라이브러리 → 서드파티 → 로컬 순서로 그룹화

#### 6.2 함수 및 클래스
```python
# ✅ 올바른 예시
def get_production_data(item_code: str) -> Dict[str, Any]:
    """
    Retrieve production data for a specific item.
    
    Args:
        item_code: The unique item identifier.
        
    Returns:
        Dictionary containing production information.
        
    Raises:
        ValueError: If item_code is invalid.
    """
    if not item_code:
        raise ValueError("Item code cannot be empty")
    return database.fetch_item(item_code)
```

**규칙:**
- 모든 공개(public) 함수는 docstring 필수 (PEP 257)
- 타입 힌트 사용 필수 (PEP 484)
- 한 줄에 함수 선언과 반환을 함께 쓰지 않기
- 비동기 함수는 `async def` 사용

#### 6.3 변수명 및 상수
```python
# ✅ 올바른 예시
class ProductionPlan:
    MAX_QUANTITY = 10000      # 상수: 대문자
    production_date = None    # 변수: 소문자_언더스코어
    
    def __init__(self, plan_name: str):
        self.plan_name = plan_name
```

**규칙:**
- 변수/메서드: `snake_case` (소문자_언더스코어)
- 클래스명: `PascalCase` (대문자로 시작)
- 상수: `SCREAMING_SNAKE_CASE` (모두 대문자)
- 비공개 메서드: `_private_method` 으로 시작

#### 6.4 주석 및 문서화
```python
# ✅ 올바른 예시
# 이 함수는 생산량을 검증합니다.
def validate_quantity(qty: int) -> bool:
    """Check if quantity is within acceptable range."""
    return 0 < qty <= MAX_QUANTITY
```

**규칙:**
- 주석은 코드 목적을 설명
- Docstring은 Google Style 또는 NumPy Style 사용
- 주석이 코드와 일치하도록 유지

### JavaScript/ECMAScript (Frontend) - 현대적 표준 준수

#### 6.5 기본 규칙
- **라인 길이**: 최대 80자
- **들여쓰기**: 2 스페이스
- **세미콜론**: 항상 사용
- **따옴표**: 싱글 쿼트(') 사용

#### 6.6 함수 및 모듈
```javascript
// ✅ 올바른 예시
/**
 * Fetch production data from API.
 * 
 * @async
 * @param {string} itemCode - The item identifier
 * @returns {Promise<Object>} Production data
 * @throws {Error} If API request fails
 */
export async function fetchProductionData(itemCode) {
  try {
    const response = await api.get(`/production/${itemCode}`);
    return response.data;
  } catch (error) {
    console.error('[API Error]', error);
    throw error;
  }
}
```

**규칙:**
- 모든 공개 함수는 JSDoc 주석 필수
- 비동기 함수는 `async/await` 사용
- 에러 처리는 try-catch 또는 .catch() 사용
- 화살표 함수는 한 줄 표현식에만 사용

#### 6.7 변수명 및 상수
```javascript
// ✅ 올바른 예시
const MAX_TIMEOUT = 5000;     // 상수: SCREAMING_SNAKE_CASE
const apiUrl = 'http://...';  // 변수: camelCase
const ProductionPlan = {};    // 객체/클래스: PascalCase
```

**규칙:**
- 변수/함수: `camelCase` (첫 글자 소문자, 다음 글자부터 대문자)
- 상수: `SCREAMING_SNAKE_CASE` (모두 대문자)
- 클래스/컴포넌트: `PascalCase` (첫 글자 대문자)
- 비공개 변수: `_privateVar` 으로 시작

### 6.8 공통 규칙 (Python & JavaScript)

#### 에러 처리
```python
# Python ✅
try:
    result = api.call()
except ConnectionError as e:
    logger.error(f'API connection failed: {e}')
    raise
```

```javascript
// JavaScript ✅
try {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
} catch (error) {
  console.error('[API Error]', error);
  throw error;
}
```

#### 로깅
```python
# Python ✅
import logging
logger = logging.getLogger(__name__)
logger.info('Processing item: %s', item_code)
logger.error('Failed to fetch data', exc_info=True)
```

```javascript
// JavaScript ✅
console.debug('[API Request]', method, url);
console.error('[API Error]', status, message);
```

### 6.9 도구 및 자동화

#### Python
```bash
# 설설 (PEP 8 자동 수정)
pip install black flake8 isort

# 코드 포맷팅
black .

# Linting (문제 검사)
flake8 . --max-line-length=99

# Import 정렬
isort .
```

#### JavaScript
```bash
# 설정
npm install --save-dev eslint prettier

# 코드 포맷팅
npm run format

# Linting
npm run lint
```

### 6.10 CI/CD 승인 기준
- [x] PEP 8 준수 (Python): `flake8` 실행 0 에러
- [x] ECMAScript 준수 (JavaScript): `eslint` 실행 0 에러
- [x] 유닛 테스트: 최소 80% 통과
- [x] Docstring/JSDoc: 모든 공개 함수/모듈 필수
- [x] 타입 힌트 (Python): 신규 코드 100%
- [x] 에러 처리: 모든 API 호출에 필수

---
*최종 업데이트: 2026-02-12*
*작성자: iamywl (Kyungpook National Univ.)*
*코딩 표준 추가: 2026-02-12*
