import os
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# 1. 환경변수(.env) 불러오기
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

def get_stock_data(ticker_symbol):
    """yfinance를 이용해 주식 데이터를 가져오는 함수"""
    print(f"[{ticker_symbol}] 데이터 수집 시작...")
    ticker = yf.Ticker(ticker_symbol)
    
    # 최근 1달 데이터 가져오기
    df = ticker.history(period="1mo")
    
    # 인덱스(Date)를 일반 컬럼으로 빼고, 종목 코드 컬럼 추가
    df.reset_index(inplace=True)
    df['Ticker'] = ticker_symbol
    
    # DB에 넣기 좋게 컬럼명을 소문자로 변경
    df.columns = [c.lower() for c in df.columns]
    
    return df

def load_to_db(df, table_name):
    """DataFrame을 PostgreSQL 데이터 웨어하우스에 적재하는 함수"""
    # SQLAlchemy를 이용해 DB 엔진 생성 (PostgreSQL 연결 문자열)
    db_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(db_url)
    
    print(f"데이터베이스 연결 성공! '{table_name}' 테이블에 데이터 적재 중...")
    
    # DataFrame을 SQL 테이블로 바로 밀어넣기
    # if_exists='append'는 기존 데이터 아래에 추가하라는 뜻!
    df.to_sql(name=table_name, con=engine, if_exists='append', index=False)
    
    print(" 데이터 적재 완료!")

if __name__ == "__main__":
    # 애플(AAPL) 주식 데이터 테스트
    target_ticker = "AAPL"
    
    # 1. 데이터 추출 (Extract) & 변환 (Transform)
    stock_df = get_stock_data(target_ticker)
    
    # 2. 데이터 적재 (Load)
    load_to_db(stock_df, "daily_stock_prices")