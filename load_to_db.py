import pandas as pd
from sqlalchemy import create_engine, text

# ★★★ 아까 GCP에서 복사한 공개 IP 주소로 꼭 변경해줘! (따옴표 유지) ★★★
import os
# ... 다른 import 생략 ...

# ==========================================
# 1. DB 접속 정보 설정 (환경 변수 시스템 적용)
# ==========================================
# os.environ.get('변수명', '기본값')
# Cloud Run에 올라가면 구글 서버가 진짜 IP와 비번을 주입해주고,
# 로컬에서 테스트할 때는 기본값으로 설정된 가짜 IP와 비번이 사용됨
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')       # <--- 진짜 IP 지우고 로컬 주소나 가짜값 넣기
DB_USER = os.environ.get('DB_USER', 'your_db_user')    # <--- 가짜 이름으로 변경
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password_here!') # <--- 진짜 비번 절대 삭제!
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'stock_data')

# 파이썬과 DB를 연결해주는 엔진
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# 테이블(서랍장) 뼈대 만들기
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

print(" 구글 클라우드 DB에 접속 중...")
with engine.connect() as conn:
    conn.execute(text(create_table_query))
    conn.commit()
print(" 테이블(서랍장) 생성 완료!")

# CSV 읽어서 DB로 쏘아 올리기
try:
    df = pd.read_csv("sp500_top5_stock_data.csv")
    
    # DB 컬럼명에 맞게 이름 변경
    df = df.rename(columns={
        'Date': 'price_date', 'Open': 'open_price', 'High': 'high_price',
        'Low': 'low_price', 'Close': 'close_price', 'Volume': 'volume', 'Ticker': 'ticker'
    })
    
    # 넣을 컬럼만 쏙쏙 뽑기
    columns_to_insert = ['ticker', 'price_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']
    df = df[columns_to_insert]

    print(f" 데이터를 DB에 넣는 중...")
    
    # 마법의 함수 to_sql: 데이터프레임을 통째로 DB에 밀어넣기
    df.to_sql(name='stock_prices', con=engine, if_exists='append', index=False)
    print(" 데이터 적재(Load) 100% 성공!!")

except Exception as e:
    print(f" 에러 발생: {e}")