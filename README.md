
---

```markdown
# 📈 S&P 500 주식 데이터 자동 수집 및 클라우드 적재 파이프라인 (ETL)

> **GCP(Google Cloud Platform) 기반의 서버리스 아키텍처를 활용하여 매일 자동으로 S&P 500 주가 데이터를 수집, 정제 후 RDB에 적재하는 End-to-End 데이터 파이프라인 프로젝트입니다.**

<br>

## 💡 프로젝트 아키텍처 (Architecture)

본 프로젝트는 비용 최적화와 인프라 관리 부담을 최소화하기 위해 24시간 서버를 켜두는 방식 대신, 필요할 때만 자원을 할당받아 수행되는 **서버리스(Serverless)** 및 **컨테이너(Container)** 아키텍처로 설계되었습니다.



1. **알람시계 (Cloud Scheduler)**: 크론탭(`0 9 * * 1-5`) 스케줄에 따라 매일 아침 9시(KST)마다 Cloud Run Job에 트리거 신호를 보냅니다.
2. **실행기 (Cloud Run Jobs)**: 신호를 받으면 Artifact Registry에서 빌드된 Docker 이미지를 인스턴스로 구동해 딱 1분간 파이썬 스크립트를 실행하고 자동 소멸합니다. (비용 극대화 절감)
3. **저장소 (Cloud SQL)**: 수집 및 정제가 완료된 데이터를 PostgreSQL 데이터베이스 테이블에 안전하게 적재합니다.

---

## 🛠️ 기술 스택 (Tech Stacks)

| 분류 | 기술 기술 | 선택 이유 |
| :--- | :--- | :--- |
| **Language** | `Python 3.12` | Pandas, yfinance 등 데이터 다듬기 및 API 라이브러리 생태계 풍부 |
| **Database** | `PostgreSQL` | 주가 데이터의 무결성과 시계열 정밀도를 보장하기 위한 RDB 선택 |
| **Cloud** | `GCP (Cloud SQL, Cloud Run, Artifact Registry)` | 서버리스 환경(Jobs)을 통한 프리티어 내 비용 최적화 및 뛰어난 연동성 |
| **DevOps** | `Docker`, `Git/GitHub` | 로컬 가상환경 의존성을 완전히 격리하고, 어디서든 구동 가능한 무적의 이미지 패키징 |

---

## 📂 프로젝트 구조 (Directory Structure)

```text
.
├── pipeline.py         # 데이터 수집(Extract), 전처리(Transform), 적재(Load) 통합 스크립트
├── Dockerfile          # 파이썬 가상환경 및 코드 패키징용 도커 레시피 파일
├── requirements.txt    # 파이프라인 구동에 필요한 파이썬 라이브러리 명세서
└── .gitignore          # 로컬 가상환경 및 클라우드 보안 자격 증명(json, txt) 파일 유출 차단막

```

---

##  주요 기능 및 핵심 고도화 포인트

### 1. 멱등성(Idempotency) 보장을 위한 `Upsert` 로직 도입

* **문제:** 매일 같은 수집 범위(최근 1개월)의 배치(Batch) 작업이 돌면서, RDB의 기본키(`PRIMARY KEY (ticker, price_date)`) 제약 조건을 위배하는 `UniqueViolation` 중복 에러 발생.
* **해결:** 데이터를 무작정 누적(`append`)하는 대신, PostgreSQL 전용 대량 `ON CONFLICT (ticker, price_date) DO UPDATE SET...` 구문을 적용. 이미 존재하는 날짜의 주가는 최신 정보로 리프레시하고, 새로운 데이터는 삽입하는 **Upsert 시스템을 구축하여 파이프라인의 안전성 확보.**

### 2. 가상환경 세팅 지옥 탈출: Docker 컨테이너화

* **문제:** 로컬 작업 PC 이동 시 발생하는 OS 환경 변수(PATH) 꼬임 문제 및 외부 라이브러리(`lxml`, `html5lib` 등) 누락 에러 직면.
* **해결:** `python:3.12-slim` 베이스 이미지 기반의 `Dockerfile`을 직접 작성하여 실행 환경을 격리. 로컬 PC에 구애받지 않고, 구글 클라우드 인프라 어디서든 똑같이 작동하는 이식성 높은 환경 마련.

### 3. 하드코딩 금지 및 철저한 보안 자격 증명(Credentials) 관리

* **문제:** 깃허브(GitHub) 저장소에 구글 서비스 계정 키(`.json`), 깃허브 액세스 토큰(`.txt`), DB 접속 정보가 유출될 경우 클라우드 자원 해킹 및 요금 폭탄 리스크 존재.
* **해결:** * `pipeline.py` 내부 DB 매핑 코드를 `os.environ.get()` 기반의 **환경 변수 구조**로 전면 리팩토링.
* 깃허브에는 가짜 Fallback 주소(`127.0.0.1`)만 노출되게 설계하고, 진짜 IP와 패스워드는 GCP Cloud Run 설정창 내부에만 안전하게 주입.
* `.gitignore` 설정을 통해 원천적으로 로컬 내 민감 키 파일이 Git 추적에 담기지 않도록 방어막 구축.



---

## 실행 방법 (Usage)

### 로컬에서 Docker 빌드 및 테스트

```bash
# 1. 도커 이미지 빌드
docker build -t stock-pipeline:v1 .

# 2. 컨테이너 수동 실행 테스트
docker run --name stock-app stock-pipeline:v1

```

### GCP Artifact Registry 배포

```bash
# 1. GCP 도커 레지스트리 인증인증
gcloud auth configure-docker asia-northeast3-docker.pkg.dev

# 2. 이미지 태그 생성 및 푸시
docker tag stock-pipeline:v1 asia-northeast3-docker.pkg.dev/[YOUR_PROJECT_ID]/stock-repo/stock-pipeline:v1
docker push asia-northeast3-docker.pkg.dev/[YOUR_PROJECT_ID]/stock-repo/stock-pipeline:v1

```

```

---

