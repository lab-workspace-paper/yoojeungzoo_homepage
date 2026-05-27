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

# [핵심] 환경 변수 대신 물리적 경로로 로컬/서버 완벽 자동 감지
LOCAL_BASE_PATH = r"G:\내 드라이브\pai_homepage\static"
is_server = not os.path.exists(LOCAL_BASE_PATH)

BUCKET_NAME = "yoojeongzoo-library-storage"

if is_server:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
else:
    storage_client = None
    bucket = None

def parse_paper_filename(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    
    category = parts[0] if len(parts) > 0 else "연구"
    year = parts[-1] if len(parts) > 3 else "-"
    publisher = parts[-2] if len(parts) > 2 else "-"
    
    if len(parts) > 3:
        title = "_".join(parts[1:-2])
    elif len(parts) > 1:
        title = parts[1]
    else:
        title = name_without_ext
        
    return {
        'name': name_without_ext,
        'category': category,
        'title': title,
        'publisher': publisher,
        'year': year,
        'file': filename
    }

def scan_local_papers():
    published, wip = [], []
    if is_server and bucket:
        # 클라우드 환경: GCS 스토리지 탐색
        blobs = bucket.list_blobs(prefix='static/papers/')
        for blob in blobs:
            file_name = blob.name.split('/')[-1]
            if not file_name or '.' not in file_name: continue
            
            if '/published/' in blob.name and file_name.lower().endswith('.pdf'):
                published.append(parse_paper_filename(file_name))
            elif '/wip/' in blob.name and file_name.lower().endswith('.png'):
                wip.append(parse_paper_filename(file_name))
    else:
        # 로컬 환경: G드라이브 물리 탐색
        pub_dir = os.path.join(LOCAL_BASE_PATH, 'papers', 'published')
        wip_dir = os.path.join(LOCAL_BASE_PATH, 'papers', 'wip')
        if os.path.exists(pub_dir):
            for f in os.listdir(pub_dir):
                if f.lower().endswith('.pdf'):
                    published.append(parse_paper_filename(f))
        if os.path.exists(wip_dir):
            for f in os.listdir(wip_dir):
                if f.lower().endswith('.png'):
                    wip.append(parse_paper_filename(f))
    return published, wip

def scan_local_books():
    books = []
    if is_server and bucket:
        blobs = bucket.list_blobs(prefix='static/books/pending/')
        for blob in blobs:
            file_name = blob.name.split('/')[-1]
            if file_name.lower().endswith('.pdf'):
                books.append({'title': file_name.replace('.pdf', ''), 'file': file_name})
    else:
        books_dir = os.path.join(LOCAL_BASE_PATH, 'books', 'pending')
        if os.path.exists(books_dir):
            for f in os.listdir(books_dir):
                if f.lower().endswith('.pdf'):
                    books.append({'title': f.replace('.pdf', ''), 'file': f})
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

@app.route('/api/content/<string:filename>', methods=['GET'])
def get_sub_content(filename):
    return render_template(filename)

@app.route('/api/academy-video/<filename>')
def get_academy_video(filename):
    if is_server and bucket:
        blob = bucket.blob(f"static/academy_videos/{filename}")
        url = blob.generate_signed_url(expiration=timedelta(minutes=60))
        return jsonify({'url': url})
    else:
        return jsonify({'url': f"/static/academy_videos/{filename}"})

application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)