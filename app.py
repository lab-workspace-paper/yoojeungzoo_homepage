import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask import jsonify

load_dotenv()

app = Flask(__name__)
CORS(app)

port = int(os.environ.get("PORT", 8080))

# 폴더 경로 정의
BASE_PATH = os.path.join(app.root_path, 'static')

def scan_local_papers():
    published_dir = os.path.join(BASE_PATH, 'papers', 'published')
    wip_dir = os.path.join(BASE_PATH, 'papers', 'wip')
    
    # 1. published: .pdf 전용 스캔
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
            
    # 2. wip: .png 전용 스캔
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
    # books 하위의 모든 .pdf 파일 재귀적 스캔
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
    # host는 0.0.0.0으로 유지하고, 포트는 위에서 정의한 port 변수를 사용
    app.run(host='0.0.0.0', port=port)