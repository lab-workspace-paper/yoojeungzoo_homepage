# 파이썬 경량 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필수 빌드 도구 설치 및 캐시 정리
RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*

# 종속성 파일 복사 및 설치 (레이어 캐싱 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 데이터 폴더(static)를 제외한 핵심 코드만 명시적으로 복사
# 이렇게 하면 static 폴더 내부의 대용량 자료가 빌드에 포함되지 않습니다
COPY app.py .
COPY templates/ ./templates/

# Gunicorn 서버 실행 (시간 제한 없음)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "0", "app:application"]