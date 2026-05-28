FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*

# 종속성 파일을 먼저 설치 (이 단계는 거의 변하지 않으므로 캐싱됨)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 이제 코드와 디자인 리소스를 복사 (이후 푸시부터는 이 단계만 실행되어 3분 내로 종료됨)
COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "0", "app:application"]