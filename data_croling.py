# import pandas as pd
# import requests
# from io import StringIO
# import yfinance as yf
# import time

# url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
# headers = {'User-Agent': 'Mozilla/5.0'}

# print("🌐 S&P 500 종목 가져오는 중...")
# response = requests.get(url, headers=headers)
# sp500_table = pd.read_html(StringIO(response.text))[0]
# top_5_tickers = sp500_table['Symbol'].tolist()[:5]

# all_data = []
# for ticker in top_5_tickers:
#     print(f"[{ticker}] 주가 다운로드 중...")
#     df = yf.download(ticker, period="1mo", progress=False)
#     df['Ticker'] = ticker 
#     all_data.append(df)
#     time.sleep(1)

# final_df = pd.concat(all_data)
# final_df.to_csv("sp500_top5_stock_data.csv")
# print("🎉 CSV 데이터 수집 완료!")

import pandas as pd
import requests
from io import StringIO
import yfinance as yf
import time

url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
headers = {'User-Agent': 'Mozilla/5.0'}

print(" S&P 500 종목 가져오는 중...")
response = requests.get(url, headers=headers)
sp500_table = pd.read_html(StringIO(response.text))[0]
top_5_tickers = sp500_table['Symbol'].tolist()[:5]

all_data = []
for ticker in top_5_tickers:
    print(f"[{ticker}] 깔끔하게 주가 다운로드 중...")
    
    #  [핵심!] yf.download 대신 history()를 쓰면 3단 꼬임이 절대 발생 안 함!
    stock = yf.Ticker(ticker)
    df = stock.history(period="1mo")
    
    if df.empty:
        continue
        
    df = df.reset_index() # 인덱스에 숨어있는 Date를 정식 컬럼으로 빼내기!
    
    # 타임존(시간대) 글자들 떼어내고 딱 '년-월-일' 날짜만 깔끔하게 남기기
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
    elif 'Datetime' in df.columns:
        df.rename(columns={'Datetime': 'Date'}, inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        
    df['Ticker'] = ticker 
    
    # DB에 넣을 딱 7개 컬럼만 예쁘게 골라내기
    cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Ticker']
    df = df[cols]
    
    all_data.append(df)
    time.sleep(1)

# 하나로 합치고 저장!
final_df = pd.concat(all_data)
final_df.to_csv("sp500_top5_stock_data.csv", index=False)
print(" 3단 콤보 박살! 1줄짜리 완벽한 CSV 데이터 수집 완료!")