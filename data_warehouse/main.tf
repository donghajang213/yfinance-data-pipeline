# 1. Cloud SQL 인스턴스 (서버 본체) 생성
resource "google_sql_database_instance" "warehouse_instance" {
  name             = "yfinance-dw-instance"
  database_version = "POSTGRES_15"
  region           = "asia-northeast3"

  settings {
    tier = "db-f1-micro" # 가장 저렴한 무료/학습용 스펙
  }
  
  # 실습용이므로 삭제가 쉽도록 설정 (운영 환경에서는 true로 해야 함)
  deletion_protection = false 
}

# 2. 인스턴스 안에 실제 데이터베이스 생성
resource "google_sql_database" "finance_db" {
  name     = "stock_data"
  instance = google_sql_database_instance.warehouse_instance.name
}

# 3. 데이터베이스 접속용 유저 생성
resource "google_sql_user" "db_user" {
  name     = "admin_user"
  instance = google_sql_database_instance.warehouse_instance.name
  password = "password123!" # <- 나중에 환경변수 등으로 숨길 거지만, 일단 임시로 사용할 비밀번호로 바꿔줘!
}