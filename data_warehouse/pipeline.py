import os
import yfinance as yf
import pandas as pd
from google.cloud import bigquery # PostgreSQL용 sqlalchemy 대신 빅쿼리 라이브러리로 교체!
from dotenv import load_dotenv # 추가

load_dotenv()  # .env 파일에서 환경 변수 로드

def get_stock_data(ticker_symbol):
    """yfinance를 이용해 주식 데이터를 가져오는 함수"""
    print(f"[{ticker_symbol}] 데이터 수집 시작...")
    ticker = yf.Ticker(ticker_symbol)
    
    # 최근 1달 데이터 가져오기
    df = ticker.history(period="1mo")
    
    # 인덱스(Date)를 일반 컬럼으로 빼고, 종목 코드 컬럼 추가
    df.reset_index(inplace=True)
    df['Ticker'] = ticker_symbol
    
    # ★추가된 부분: BigQuery는 날짜 형식(Timezone)에 엄청 예민해! 
    # yfinance의 복잡한 날짜 시간대 정보를 깔끔한 'YYYY-MM-DD' DATE 타입으로 깎아주는 로직
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    # DB에 넣기 좋게 컬럼명을 소문자로 변경
    df.columns = [c.lower() for c in df.columns]
    
    # 빅쿼리 분석에 불필요한 배당금/액면분할 컬럼은 깔끔하게 제거
    if 'dividends' in df.columns:
        df.drop(columns=['dividends', 'stock splits'], inplace=True, errors='ignore')
        
    return df

def load_to_bigquery(df, project_id, dataset_id, table_name):
    """DataFrame을 Google BigQuery 데이터 웨어하우스에 적재하는 함수"""
    
    # 1. 빅쿼리 통신 클라이언트 생성
    # Cloud Run에 올라가면 구글이 알아서 인증해주기 때문에 복잡한 비밀번호(.env)가 필요 없어!
    client = bigquery.Client(project=project_id)
    
    # 2. 데이터를 꽂아넣을 목적지 주소 조립 (프로젝트ID.데이터셋이름.테이블이름)
    table_id = f"{project_id}.{dataset_id}.{table_name}"
    
    # 3. 빅쿼리 적재 규칙 설정
    job_config = bigquery.LoadJobConfig(
        # 테이블이 없으면 자기가 알아서 만들고, 있으면 밑에 계속 추가(Append)하라는 뜻!
        write_disposition="WRITE_APPEND", 
    )
    
    print(f"📦 BigQuery 연결 시도! '{table_id}' 테이블에 데이터 적재 중...")
    
    # 4. DataFrame을 빅쿼리로 다이렉트 슛!
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # 구글 서버에서 데이터 적재가 완료될 때까지 잠깐 기다림
    
    print(f"✅ 데이터 적재 완료! (총 {job.output_rows}행이 빅쿼리에 안전하게 들어갔어!)")

if __name__ == "__main__":
    # 포트폴리오용 S&P 500 대표 5대장 종목
    target_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    
    # ⚠️ [수정 주의] 본인의 진짜 GCP 프로젝트 ID로 바꿔줘! (예: stock-data-pipeline-496004)
    GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-project-id") 
    BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "stock_dataset")      # 우리가 만들 빅쿼리 빈 통 이름
    BQ_TABLE_NAME = os.environ.get("BQ_TABLE_NAME") # 데이터가 들어갈 테이블 이름
    
    for ticker in target_tickers:
        # 1. 데이터 추출 (Extract) & 변환 (Transform)
        stock_df = get_stock_data(ticker)
        
        # 2. 데이터 적재 (Load)
        load_to_bigquery(stock_df, GCP_PROJECT_ID, BQ_DATASET_ID, BQ_TABLE_NAME)