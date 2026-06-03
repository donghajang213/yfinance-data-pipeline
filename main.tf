# 1. GCP 프로바이더 설정
provider "google" {
  project     = "stock-data-pipeline-496004" # 네 프로젝트 ID (그대로 쓰면 됨!)
  region      = "asia-northeast3"            # 한국 서울 리전
}

# 2. Cloud SQL (PostgreSQL) 인스턴스 생성
resource "google_sql_database_instance" "stock_db_instance" {
  name             = "stock-db-instance"
  database_version = "POSTGRES_15"           
  region           = "asia-northeast3"

  settings {
    tier = "db-f1-micro" # 가장 저렴한 테스트용 사양
    
    # 어디서든 접속 가능하게 설정
    ip_configuration {
      authorized_networks {
        name  = "all"
        value = "0.0.0.0/0"
      }
    }
  }
  deletion_protection = false # 나중에 삭제하기 쉽게 방지 기능 꺼둠
}

# 3. 실제 데이터베이스 생성
resource "google_sql_database" "stock_db" {
  name     = "stock_data"
  instance = google_sql_database_instance.stock_db_instance.name
}

# 4. DB 사용자 생성
resource "google_sql_user" "users" {
  name     = "admin"
  instance = google_sql_database_instance.stock_db_instance.name
  password = "password123!" # 필요하면 비밀번호 변경해!
}