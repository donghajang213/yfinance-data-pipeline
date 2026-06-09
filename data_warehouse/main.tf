
# 1. BigQuery 데이터셋 (데이터가 들어갈 가장 큰 폴더/창고 역할)
resource "google_bigquery_dataset" "stock_dataset" {
  dataset_id                  = "stock_dataset"                  # 파이썬 코드에 적은 BQ_DATASET_ID와 동일해야 함
  friendly_name               = "S&P 500 Stock Dataset"
  description                 = "S&P 500 주식 데이터를 적재하는 빅쿼리 데이터셋"
  location                    = "asia-northeast3"                # 데이터가 물리적으로 저장될 위치 (서울)
  
  # 실무에서는 false로 하지만, 포트폴리오용이므로 나중에 깔끔하게 지우기 위해 true 설정
  delete_contents_on_destroy  = true 
}

# (주의!) 테이블(Table) 생성 코드는 굳이 테라폼에 안 적어도 돼!
# 왜냐하면 우리의 똑똑한 파이썬 코드(pipeline.py)가 실행될 때 
# "어? 테이블이 없네? 내가 Pandas 데이터 모양대로 알아서 만들게!" 하고 자동 생성해주거든.