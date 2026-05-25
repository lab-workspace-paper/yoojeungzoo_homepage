# 파이썬 3.11 버전 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# Gunicorn으로 서버 실행
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "0", "app:application"]