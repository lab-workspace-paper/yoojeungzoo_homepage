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
    if is_server:
        try:
            if bucket is None:
                raise ValueError("GCS 버킷 객체가 생성되지 않았습니다.")
                
            blobs = bucket.list_blobs(prefix='static/papers/')
            blob_count = 0
            for blob in blobs:
                blob_count += 1
                file_name = blob.name.split('/')[-1]
                if not file_name or '.' not in file_name: continue
                
                if '/published/' in blob.name and file_name.lower().endswith('.pdf'):
                    published.append(parse_paper_filename(file_name))
                elif '/wip/' in blob.name and file_name.lower().endswith('.png'):
                    wip.append(parse_paper_filename(file_name))
            
            # 클라우드에서 파일을 1개도 못 찾았을 경우 화면에 원인 출력
            if blob_count == 0:
                published.append({
                    'name': 'debug', 'category': '시스템 진단', 
                    'title': 'GCS 통신은 성공했으나, static/papers/ 하위에서 파일을 1개도 찾지 못했습니다.',
                    'publisher': BUCKET_NAME, 'year': '경로점검', 'file': ''
                })
        except Exception as e:
            # 권한 오류 등 치명적 에러 발생 시 화면에 에러 내용 출력
            published.append({
                'name': 'error', 'category': '오류 발생', 
                'title': f'클라우드 권한/통신 에러가 발생했습니다: {str(e)}',
                'publisher': '접근불가', 'year': '에러', 'file': ''
            })
    else:
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
    if is_server:
        try:
            blobs = bucket.list_blobs(prefix='static/books/pending/')
            blob_count = 0
            for blob in blobs:
                blob_count += 1
                file_name = blob.name.split('/')[-1]
                if file_name.lower().endswith('.pdf'):
                    books.append({'title': file_name.replace('.pdf', ''), 'file': file_name})
            
            if blob_count == 0:
                books.append({'title': 'GCS 통신 성공. 단, static/books/pending/ 경로에 파일이 없습니다.', 'file': ''})
        except Exception as e:
            books.append({'title': f'클라우드 권한 에러: {str(e)}', 'file': ''})
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