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

BUCKET_NAME = "yoojeongzoo-library-storage"

if is_server:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
else:
    storage_client = None
    bucket = None
    BASE_PATH = r"G:\내 드라이브\pai_homepage\static"

# 파일명 파싱 함수 (로컬/서버 공통)
def parse_paper_filename(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    # 기본값 설정
    title = name_without_ext
    category = "연구"
    publisher = "-"
    year = "-"
    
    if len(parts) > 1:
        category = parts[0]
        title = "_".join(parts[1:])
    if len(parts) > 2:
        publisher = parts[-2]
        year = parts[-1]
    return {'name': name_without_ext, 'category': category, 'title': title, 'publisher': publisher, 'year': year, 'file': filename}

def scan_local_papers():
    published_list = []
    wip_list = []
    
    if is_server:
        blobs = bucket.list_blobs(prefix='static/papers/')
        for blob in blobs:
            if not blob.name.lower().endswith(('.pdf', '.png')): continue
            file_name = blob.name.split('/')[-1]
            
            # published는 .pdf, wip은 .png
            if '/published/' in blob.name and file_name.lower().endswith('.pdf'):
                published_list.append(parse_paper_filename(file_name))
            elif '/wip/' in blob.name and file_name.lower().endswith('.png'):
                wip_list.append(parse_paper_filename(file_name))
    else:
        pub_dir = os.path.join(BASE_PATH, 'papers', 'published')
        wip_dir = os.path.join(BASE_PATH, 'papers', 'wip')
        if os.path.exists(pub_dir):
            for f in os.listdir(pub_dir):
                if f.lower().endswith('.pdf'): published_list.append(parse_paper_filename(f))
        if os.path.exists(wip_dir):
            for f in os.listdir(wip_dir):
                if f.lower().endswith('.png'): wip_list.append(parse_paper_filename(f))
    return published_list, wip_list

def scan_local_books():
    books = []
    if is_server:
        blobs = bucket.list_blobs(prefix='static/books/pending/')
        for blob in blobs:
            if blob.name.lower().endswith('.pdf'):
                file_name = blob.name.split('/')[-1]
                books.append({'title': file_name.replace('.pdf', ''), 'file': file_name})
    else:
        books_dir = os.path.join(BASE_PATH, 'books', 'pending')
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
    # 폴더명을 academy_videos로 통일
    path = f"static/academy_videos/{filename}"
    if is_server:
        blob = bucket.blob(path)
        url = blob.generate_signed_url(expiration=timedelta(minutes=60))
        return jsonify({'url': url})
    return jsonify({'url': f"/{path}"})

application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)