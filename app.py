from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests

app = Flask(__name__)
CORS(app)

# 규정 데이터 로드
with open('regulations.json', 'r', encoding='utf-8') as f:
    regulations_data = json.load(f)

# Gemma4 로컬 서버 설정
OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "gemma2"  # ollama에서 실행 중인 모델명

def get_regulations_text():
    """규정 데이터를 텍스트로 변환"""
    text = "코디세이 교육생 기본 규칙:\n\n"
    for category, items in regulations_data['규정이']['categories'].items():
        text += f"## {category}\n"
        for item in items:
            text += f"Q: {item['question']}\nA: {item['answer']}\n\n"
    return text

@app.route('/api/ask', methods=['POST'])
def ask_regulation():
    """사용자 질문에 규정에 기반한 답변"""
    data = request.json
    user_question = data.get('question', '')
    
    if not user_question:
        return jsonify({'error': '질문을 입력해주세요'}), 400
    
    # 규정 데이터를 프롬프트에 포함
    regulations_text = get_regulations_text()
    
    prompt = f"""당신은 코디세이 교육 센터의 친절한 규정 안내 봇 '규정이'입니다.

다음은 교육생이 지켜야 할 기본 규칙들입니다:

{regulations_text}

위의 규칙을 참고하여 다음 질문에 친절하고 명확하게 답변해주세요:
사용자 질문: {user_question}

답변 시 주의사항:
1. 관련 규정을 명확히 인용하세요
2. 이해하기 쉽게 설명하세요
3. 추가 팁이 있으면 제공하세요
4. 규칙에 없는 내용은 "운영진에게 물어봐주세요"라고 하세요
"""
    
    try:
        response = requests.post(OLLAMA_API, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7
        })
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('response', '답변을 생성할 수 없습니다.')
            return jsonify({
                'question': user_question,
                'answer': answer,
                'status': 'success'
            })
        else:
            return jsonify({
                'error': f'Gemma4 응답 오류: {response.status_code}'
            }), 500
    
    except requests.exceptions.ConnectionError:
        return jsonify({
            'error': 'Ollama 서버에 연결할 수 없습니다. (localhost:11434 확인)'
        }), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/regulations', methods=['GET'])
def get_regulations():
    """규정 데이터 반환"""
    return jsonify(regulations_data)

@app.route('/health', methods=['GET'])
def health():
    """헬스 체크"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
