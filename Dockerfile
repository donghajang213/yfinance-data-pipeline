# 1. 베이스 이미지 설정 (가볍고 안정적인 파이썬 3.12 슬림 버전)
FROM python:3.12-slim

# 2. 컨테이너 내부의 기본 작업 디렉토리 설정
WORKDIR /app

# 3. 패키지 영수증을 먼저 복사하고 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 우리가 짠 파이썬 코드 소스파일을 컨테이너 안으로 복사
COPY pipeline.py .

# 5. 이 도커 상자가 실행(Run)될 때 자동으로 실행할 명령어 지정
CMD ["python", "pipeline.py"]