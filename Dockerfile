# 파이썬 경량 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필수 빌드 도구 설치 및 캐시 정리
RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*

# 종속성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 핵심 코드 및 디자인 리소스(static, templates) 전체 복사
COPY app.py .
COPY templates/ ./templates/
# 여기에 static 폴더를 포함하도록 명령어를 추가합니다
COPY static/ ./static/

# Gunicorn 서버 실행
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "0", "app:application"]