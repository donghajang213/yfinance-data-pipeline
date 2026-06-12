
---

```markdown
# 📈 US Tech Stock Data Pipeline & BI Dashboard

> **IaC(Terraform), 워크플로우 오케스트레이션(Airflow), 클라우드 데이터 웨어하우스(GCP BigQuery), 그리고 BI(Superset)를 통합하여 매일 자동으로 S&P 500 빅테크 주식 데이터를 수집하고 시각화하는 End-to-End 데이터 파이프라인 프로젝트입니다.**

<br>

## 🏗️ 1. 프로젝트 아키텍처 (Architecture)

본 프로젝트는 데이터 수집부터 적재, 시각화에 이르는 전 과정을 도커(Docker) 컨테이너로 격리하여 로컬 환경 의존성을 없애고, Apache Airflow를 통해 스케줄링을 자동화한 아키텍처입니다.

```text
[Yahoo Finance API] 
       │ (Python / Pandas)
       ▼
[Apache Airflow] ─── (GCP IAM Secure Auth) ───► [GCP BigQuery Warehouse]
 (Docker Container)                              (Terraform managed)
                                                          │
                                                          ▼
                                                   [Apache Superset]
                                                   (Docker Visualization)

```

1. **인프라 프로비저닝 (Terraform)**: GCP BigQuery의 데이터셋과 테이블을 코드로 선언하여 안전하게 생성 및 관리합니다.
2. **오케스트레이션 (Apache Airflow)**: 크론탭(`0 9 * * *`)을 통해 매일 정해진 시간에 파이썬 데이터 수집 스크립트를 실행하고 에러 발생 시 재시도(Retry) 로직을 수행합니다.
3. **데이터 웨어하우스 (BigQuery)**: 수집 및 정제가 완료된 대용량 시계열 주식 데이터를 확장성 높은 웨어하우스에 적재합니다.
4. **시각화 대시보드 (Apache Superset)**: 적재된 데이터를 연동하여 종목별 주가 추이를 나타내는 시계열 선 차트(Time-series Line Chart)를 제공합니다.

---

## 🛠️ 2. 기술 스택 (Tech Stacks)

| 분류 | 적용 기술 | 선택 이유 |
| --- | --- | --- |
| **Language** | `Python 3.10` | Pandas, yfinance 등 데이터 전처리 및 금융 API 라이브러리 생태계 풍부 |
| **Data Warehouse** | `GCP BigQuery` | 대규모 시계열 데이터 처리에 최적화된 서버리스 데이터 웨어하우스 |
| **Orchestration** | `Apache Airflow 2.8.1` | 태스크 간의 의존성 관리 및 실패 시 재시도 로직 등 강력한 스케줄링 지원 |
| **BI / Visualization** | `Apache Superset` | 오픈소스 기반으로 다양한 차트 지원 및 BigQuery와의 매끄러운 연동성 |
| **DevOps / IaC** | `Docker`, `Terraform` | 로컬 가상환경 격리를 통한 이식성 확보 및 인프라의 코드화(IaC) |

---

## 📂 3. 프로젝트 구조 (Directory Structure)

```text
yfinance-data-pipeline/
├── .gitignore                # 클라우드 보안 자격 증명(json, .env) 유출 원천 차단막
├── README.md                 # 프로젝트 명세서
├── data_warehouse/           # 인프라 및 시각화 구성 영역
│   ├── main.tf               # Terraform BigQuery 리소스 선언 파일
│   ├── Dockerfile            # Superset BigQuery 연동 커스텀 이미지 빌드용
│   └── docker-compose.yml    # Superset 실행용 도커 컴포즈
└── airflow_env/              # 데이터 수집 및 오케스트레이션 영역
    ├── .env                  # Airflow 환경변수 및 패키지 설정
    ├── docker-compose.yaml   # Airflow 공식 도커 컴포즈
    └── dags/
        ├── stock_pipeline_dag.py # Airflow 데이터 수집 스케줄러 DAG
        └── bq_key.json       # GCP 서비스 계정 마스터키 (Git 추적 제외 대상)

```

---

## 🔐 4. 환경 변수 설정 (.env 템플릿)

보안을 위해 GCP 프로젝트 ID 및 컨테이너 권한 관련 정보는 소스코드에 하드코딩하지 않고 환경 변수로 분리하여 관리합니다. `.gitignore` 설정을 통해 원천적으로 로컬 내 민감 파일이 Git에 푸시되지 않도록 방어막을 구축했습니다.

### `airflow_env/.env` 설정 양식

```env
# 1. 파이썬 버전 명시 (yfinance 문법 충돌 방지용 커스텀 이미지)
AIRFLOW_IMAGE_NAME=apache/airflow:2.8.1-python3.10

# 2. Airflow 컨테이너 권한 설정
AIRFLOW_UID=50000

# 3. 컨테이너 구동 시 자동 설치될 파이썬 라이브러리 명세
_PIP_ADDITIONAL_REQUIREMENTS=yfinance pandas google-cloud-bigquery db-dtypes

# 4. GCP BigQuery 파이프라인 변수 (Airflow UI의 Variables로 대체 가능)
GCP_PROJECT_ID="your-gcp-project-id"
BQ_DATASET_ID="stock_dataset"
BQ_TABLE_NAME="daily_stock_prices"

```

---

## 🚀 5. 실행 방법 (Usage)

### Step 1. Apache Airflow 구축 및 스케줄러 실행

공식 `docker-compose.yaml` 파일을 다운로드하여 Airflow 클러스터를 구성합니다.

```bash
# 1. 작업 폴더 이동
cd airflow_env

# 2. Airflow 공식 도커 컴포즈 파일 다운로드
curl -LfO "[https://airflow.apache.org/docs/apache-airflow/2.8.1/docker-compose.yaml](https://airflow.apache.org/docs/apache-airflow/2.8.1/docker-compose.yaml)"

# 3. 메타데이터 DB 초기화
docker compose up airflow-init

# 4. Airflow 전체 컨테이너 백그라운드 실행
docker compose up -d

```

* **UI 접속:** `http://localhost:8080` (기본 계정: airflow / airflow)

### Step 2. Apache Superset 구축 및 시각화

BigQuery 접속용 드라이버가 포함된 커스텀 도커 이미지를 빌드하고 실행합니다.

```bash
# 1. 작업 폴더 이동
cd ../data_warehouse

# 2. 커스텀 이미지 빌드 및 실행
docker compose up -d --build

# 3. Superset 관리자 계정 생성 및 DB 초기화 (최초 1회만 실행)
docker exec -it superset superset fab create-admin
docker exec -it superset superset db upgrade
docker exec -it superset superset init

```

* **UI 접속:** `http://localhost:8088`

---

## 💡 6. 핵심 고도화 포인트 및 트러블슈팅

### 1. Airflow와 파이썬 라이브러리 간의 버전 충돌 해결

* **문제:** 최신 `yfinance` 모듈(의존성 `multitasking`)이 요구하는 파이썬 3.9 이상 문법과 공식 Airflow 도커 이미지(Python 3.8) 간의 문법 충돌로 인한 DAG 파싱 에러(`Broken DAG: TypeError`) 발생.
* **해결:** `.env` 환경 변수 파일에 `AIRFLOW_IMAGE_NAME=apache/airflow:2.8.1-python3.10`을 명시하여, 컨테이너 베이스 이미지를 파이썬 3.10 버전으로 강제 업그레이드함으로써 의존성 에러를 완벽히 해결했습니다.

### 2. 컨테이너 가상환경 격리로 인한 BI 드라이버 인식 오류 디버깅

* **문제:** Superset 컨테이너 내부에 `root` 권한으로 BigQuery 연동 패키지(`sqlalchemy-bigquery` 등)를 설치했음에도 웹 UI에서 데이터베이스 연결 에러 지속 발생.
* **해결:** 최신 Superset 도커 이미지가 보안 및 격리를 위해 컨테이너 내부에 자체 파이썬 가상환경(`/app/.venv`)을 구성하여 구동된다는 아키텍처 특성을 분석했습니다. 이에 전역 설치 대신 해당 `venv` 경로를 직접 타겟팅하여 패키지를 주입하고 빌드하는 커스텀 `Dockerfile`을 작성하여 문제를 해결했습니다.

### 3. 클라우드 권한 분리 (Principle of Least Privilege) 적용

* **문제:** Airflow에서 수집한 데이터를 BigQuery로 적재 시도 시 `403 Forbidden (Access Denied)` 에러 발생.
* **해결:** 단순 '데이터 뷰어' 권한만 부여된 시각화용 서비스 계정으로는 데이터 쓰기 작업이 원천 차단됨을 파악했습니다. 스케줄러 전용 서비스 계정에 `BigQuery 데이터 편집자(Data Editor)`와 데이터 연산을 위한 **`BigQuery 작업 사용자(bigquery.jobs.create)`** 역할을 명시적으로 분리 할당하여, 클라우드 보안성과 파이프라인 기능성을 동시에 확보했습니다.

```

```