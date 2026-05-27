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
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    BASE_PATH = "."
else:
    storage_client = None
    bucket = None
    # 로컬 환경: 기존 G드라이브 경로 유지
    BASE_PATH = r"G:\내 드라이브\pai_homepage\static"

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
    published_list = []
    wip_list = []
    
    if is_server:
        blobs = bucket.list_blobs(prefix='static/papers/')
        for blob in blobs:
            parts = blob.name.split('/')
            if len(parts) < 4: continue 
            
            category_folder = parts[2]
            file_name = parts[-1]
            if not file_name or '.' not in file_name: continue
            
            paper_info = parse_paper_filename(file_name)
            
            if category_folder == 'published':
                published_list.append(paper_info)
            elif category_folder == 'wip':
                wip_list.append(paper_info)
    else:
        # 로컬 스캔 로직
        pub_dir = os.path.join(BASE_PATH, 'papers', 'published')
        wip_dir = os.path.join(BASE_PATH, 'papers', 'wip')
        
        if os.path.exists(pub_dir):
            for f in os.listdir(pub_dir):
                if f.lower().endswith('.pdf'):
                    published_list.append(parse_paper_filename(f))
                    
        if os.path.exists(wip_dir):
            for f in os.listdir(wip_dir):
                if f.lower().endswith('.png') or f.lower().endswith('.jpg') or f.lower().endswith('.pdf'):
                    wip_list.append(parse_paper_filename(f))
                    
    return published_list, wip_list

def scan_local_books():
    books = []
    
    if is_server:
        blobs = bucket.list_blobs(prefix='static/books/')
        for blob in blobs:
            parts = blob.name.split('/')
            if len(parts) < 4: continue 
            file_name = parts[-1]
            if not file_name or '.' not in file_name: continue
            
            books.append({'title': os.path.splitext(file_name)[0], 'file': file_name})
    else:
        pending_dir = os.path.join(BASE_PATH, 'books', 'pending')
        
        if os.path.exists(pending_dir):
            for f in os.listdir(pending_dir):
                if f.lower().endswith('.pdf'):
                    books.append({'title': os.path.splitext(f)[0], 'file': f})
                    
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
    folder_path = os.path.join(app.root_path, 'static', 'credentials')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
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
        blob = bucket.blob(f"static/academy_videos/{filename}")
        url = blob.generate_signed_url(expiration=timedelta(minutes=60))
        return jsonify({'url': url})
    else:
        return jsonify({'url': f"/static/academy_videos/{filename}"})

application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)