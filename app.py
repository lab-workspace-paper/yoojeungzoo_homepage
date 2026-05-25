from flask import Flask

app = Flask(__name__)
application = app

@app.route('/')
def hello():
    return "Gov-AI-Hub Infrastructure Test: Success! 아카이브 뼈대 가동 완료."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)