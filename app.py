import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google.cloud import storage

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
        # 서버 구동 시: GCS 버킷 내 'papers/' 폴더를 직접 스캔
        published_list = []
        wip_list = []
        blobs = bucket.list_blobs(prefix='papers/')
        for blob in blobs:
            file_name = blob.name.split('/')[-1]
            if not file_name or '.' not in file_name: continue
            
            # 버킷의 papers/ 폴더 하위 구조에 따라 판별
            if file_name.upper().endswith('.PDF') and 'published' in blob.name:
                name_without_ext = os.path.splitext(file_name)[0]
                parts = name_without_ext.split('_')
                published_list.append({
                    'name': name_without_ext,
                    'category': parts[0] if len(parts) > 0 else "학술 논문",
                    'title': parts[1] if len(parts) > 1 else name_without_ext,
                    'publisher': parts[2] if len(parts) > 2 else "학회 아카이브",
                    'year': parts[3] if len(parts) > 3 else "2026"
                })
            elif file_name.upper().endswith('.PNG') and 'wip' in blob.name:
                name_without_ext = os.path.splitext(file_name)[0]
                wip_list.append({
                    'name': name_without_ext,
                    'category': "미발표",
                    'title': name_without_ext,
                    'status': "진행"
                })
        return published_list, wip_list
    else:
        # 로컬 구동 시: 기존 로직 완벽 유지
        published_dir = os.path.join(BASE_PATH, 'papers', 'published')
        wip_dir = os.path.join(BASE_PATH, 'papers', 'wip')
        published_list = []
        if os.path.exists(published_dir):
            for file in os.listdir(published_dir):
                if file.upper().endswith('.PDF'):
                    name_without_ext = os.path.splitext(file)[0]
                    parts = name_without_ext.split('_')
                    published_list.append({
                        'name': name_without_ext,
                        'category': parts[0] if len(parts) > 0 else "학술 논문",
                        'title': parts[1] if len(parts) > 1 else name_without_ext,
                        'publisher': parts[2] if len(parts) > 2 else "학회 아카이브",
                        'year': parts[3] if len(parts) > 3 else "2026"
                    })
        wip_list = []
        if os.path.exists(wip_dir):
            for file in os.listdir(wip_dir):
                if file.upper().endswith('.PNG'):
                    name_without_ext = os.path.splitext(file)[0]
                    wip_list.append({
                        'name': name_without_ext,
                        'category': "미발표",
                        'title': name_without_ext,
                        'status': "진행"
                    })
        return published_list, wip_list

def scan_local_books():
    if is_server:
        # 서버 구동 시: GCS 버킷 내 'books/' 폴더를 직접 스캔
        books = []
        blobs = bucket.list_blobs(prefix='books/')
        for blob in blobs:
            if blob.name.upper().endswith('.PDF'):
                file_name = blob.name.split('/')[-1]
                name_without_ext = os.path.splitext(file_name)[0]
                books.append({'title': name_without_ext, 'file': file_name})
        return books
    else:
        # 로컬 구동 시: 기존 로직 완벽 유지
        books_dir = os.path.join(BASE_PATH, 'books')
        books = []
        if os.path.exists(books_dir):
            for root, dirs, files in os.walk(books_dir):
                for file in files:
                    if file.upper().endswith('.PDF'):
                        name_without_ext = os.path.splitext(file)[0]
                        books.append({'title': name_without_ext, 'file': file})
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

if __name__ == '__main__':
    # 클라우드 환경에서는 자동으로 포트를 감지하여 실행
    app.run(host='0.0.0.0', port=port)

# Gunicorn이 호출할 수 있도록 app 객체를 명시
application = app