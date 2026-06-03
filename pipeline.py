import os
import pandas as pd
import requests
from io import StringIO
import yfinance as yf
import time
from sqlalchemy import create_engine, text

# ==========================================
# 1. DB 접속 정보 설정 (환경 변수 시스템 적용)
# ==========================================
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')       # <--- 진짜 IP 지우고 로컬 주소나 가짜값 넣기
DB_USER = os.environ.get('DB_USER', 'your_db_user')    # <--- 가짜 이름으로 변경
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password_here!') # <--- 진짜 비번 절대 삭제!
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'stock_data')

# ==========================================
# 2. 데이터 수집 & 정제 (Extract & Transform)
# ==========================================
url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
headers = {'User-Agent': 'Mozilla/5.0'}

print(" [Docker] S%26P 500 종목 리스트 가져오는 중...")
response = requests.get(url, headers=headers)
sp500_table = pd.read_html(StringIO(response.text))[0]
top_5_tickers = sp500_table['Symbol'].tolist()[:5]

all_data = []
for ticker in top_5_tickers:
    print(f" [Docker] [{ticker}] 주가 다운로드 중...")
    stock = yf.Ticker(ticker)
    df = stock.history(period="1mo")
    
    if df.empty:
        continue
        
    df = df.reset_index()
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
    elif 'Datetime' in df.columns:
        df.rename(columns={'Datetime': 'Date'}, inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        
    df['Ticker'] = ticker
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Ticker']]
    all_data.append(df)
    time.sleep(1)

final_df = pd.concat(all_data)

# DB 테이블 설계도와 컬럼명 맞추기
final_df = final_df.rename(columns={
    'Date': 'price_date', 'Open': 'open_price', 'High': 'high_price',
    'Low': 'low_price', 'Close': 'close_price', 'Volume': 'volume', 'Ticker': 'ticker'
})

# ==========================================
# 3. 데이터베이스 적재 (Load) - 고도화된 Upsert 로직
# ==========================================
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

create_table_query = """
CREATE TABLE IF NOT EXISTS stock_prices (
    ticker VARCHAR(10) NOT NULL,
    price_date DATE NOT NULL,
    open_price NUMERIC(20, 4),
    high_price NUMERIC(20, 4),
    low_price NUMERIC(20, 4),
    close_price NUMERIC(20, 4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, price_date)
);
"""

print(" [Docker] 구글 클라우드 DB 접속 및 테이블 확인 중...")
with engine.connect() as conn:
    conn.execute(text(create_table_query))
    conn.commit()

print(" [Docker] Upsert(ON CONFLICT) 방식으로 데이터를 최종 적재하는 중...")
try:
    #  데이터프레임의 행을 하나씩 읽으면서 PostgreSQL 전용 대량 업서트 쿼리 날리기
    with engine.connect() as conn:
        for _, row in final_df.iterrows():
            upsert_query = text("""
                INSERT INTO stock_prices (ticker, price_date, open_price, high_price, low_price, close_price, volume)
                VALUES (:ticker, :price_date, :open_price, :high_price, :low_price, :close_price, :volume)
                ON CONFLICT (ticker, price_date) 
                DO UPDATE SET 
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume,
                    created_at = CURRENT_TIMESTAMP;
            """)
            conn.execute(upsert_query, {
                'ticker': row['ticker'],
                'price_date': row['price_date'],
                'open_price': row['open_price'],
                'high_price': row['high_price'],
                'low_price': row['low_price'],
                'close_price': row['close_price'],
                'volume': row['volume']
            })
        conn.commit()
    print(" [Docker Container] 파이프라인 수집 및 적재 100% 대성공!!!")
except Exception as e:
    print(f" 적재 실패 에러 발생: {e}")