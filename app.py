import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google.cloud import storage
from datetime import timedelta

load_dotenv()

app = Flask(__name__)
CORS(app)

port = int(os.environ.get("PORT", 8080))
is_server = os.environ.get("IS_SERVER", "False") == "True"

# GCS 버킷 설정
BUCKET_NAME = "yoojeongzoo-library-storage"

if is_server:
    # 서버 환경: 클라우드 스토리지 객체 생성
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    BASE_PATH = "." # GCS 내 폴더 경로 기준점
else:
    # 로컬 환경: 기존 G드라이브 경로 유지
    storage_client = None
    bucket = None
    BASE_PATH = r"G:\내 드라이브\pai_homepage\static"

def scan_local_papers():
    if is_server:
        published_list = []
        wip_list = []
        # 'papers/'로 시작하는 모든 blob을 가져옵니다.
        blobs = bucket.list_blobs(prefix='papers/')
        for blob in blobs:
            parts = blob.name.split('/')
            if len(parts) < 3: continue # 'papers/category/filename' 구조 확인
            
            category = parts[1] # published 또는 wip
            file_name = parts[-1]
            if not file_name or '.' not in file_name: continue
            
            paper_info = {'title': os.path.splitext(file_name)[0], 'file': file_name}
            if category == 'published':
                published_list.append(paper_info)
            elif category == 'wip':
                wip_list.append(paper_info)
        return published_list, wip_list
    # (else: 로컬 로직은 그대로 유지)

def scan_local_books():
    if is_server:
        books = []
        # 'books/' 하위의 'pending/' 등을 스캔
        blobs = bucket.list_blobs(prefix='books/')
        for blob in blobs:
            parts = blob.name.split('/')
            if len(parts) < 3: continue 
            file_name = parts[-1]
            if not file_name or '.' not in file_name: continue
            
            books.append({'title': os.path.splitext(file_name)[0], 'file': file_name})
        return books
    
@app.route('/')
@app.route('/ko')
def index_ko():
    return render_template('index_ko.html')

@app.route('/api/papers-data', methods=['GET'])
def get_papers_data():
    published, wip = scan_local_papers()
    return jsonify({'published': published, 'wip': wip})

@app.route('/api/books-data', methods=['GET'])
def get_books_data():
    return jsonify({'books': scan_local_books()})

@app.route('/api/credentials-list')
def get_credentials():
    # static/credentials 폴더 경로
    folder_path = os.path.join(app.root_path, 'static', 'credentials')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # png 파일만 리스트업
    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
    return jsonify({'files': files})

@app.route('/api/content/<string:filename>', methods=['GET'])
def get_sub_content(filename):
    allowed_files = [
        'academic_papers.html', 'books_and_essays.html', 'government_projects.html', 
        'agent_academy.html', 'counseling_academy.html', 'director_identity.html'
    ]
    if filename not in allowed_files:
        return "접근 불가", 403
    return render_template(filename)

@app.route('/api/academy-video/<filename>')
def get_academy_video(filename):
    if is_server:
        # GCS 내의 영상 경로 (파일이 static/academy_video/ 아래에 있어야 함)
        blob = bucket.blob(f"static/academy_video/{filename}")
        # 서명된 URL 생성 (60분간 유효)
        url = blob.generate_signed_url(expiration=timedelta(minutes=60))
        return jsonify({'url': url})
    else:
        # 로컬: 기존 static 경로 반환
        return jsonify({'url': f"/static/academy_video/{filename}"})

# Gunicorn이 호출할 수 있도록 명시
application = app

if __name__ == '__main__':
    # 로컬 실행 시
    app.run(host='0.0.0.0', port=port)