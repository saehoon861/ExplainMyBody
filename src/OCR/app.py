"""
InBody OCR Web Application - Flask Backend
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
from pathlib import Path
import tempfile
import json
from werkzeug.utils import secure_filename

# InBody 매처 클래스를 직접 임포트
# inbody_matcher.py 파일이 같은 디렉토리에 있어야 합니다
try:
    from inbody_matcher import InBodyMatcher
except ImportError:
    print("⚠️ inbody_matcher.py 파일을 찾을 수 없습니다.")
    print("제공하신 인바디 OCR 코드를 inbody_matcher.py로 저장해주세요.")
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # CORS 활성화

# 설정
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    """허용된 파일 확장자 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        'status': 'healthy',
        'service': 'InBody OCR API'
    })


@app.route('/api/process', methods=['POST'])
def process_inbody():
    """InBody 이미지 처리 API"""
    try:
        # 파일 검증
        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'허용되지 않는 파일 형식입니다. 허용: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # 옵션 파라미터
        auto_perspective = request.form.get('auto_perspective', 'true').lower() == 'true'
        skew_threshold = float(request.form.get('skew_threshold', '15.0'))
        
        # 임시 파일로 저장
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        file.save(temp_path)
        
        try:
            # InBody 매칭 수행
            matcher = InBodyMatcher(
                auto_perspective=auto_perspective,
                skew_threshold=skew_threshold
            )
            
            results = matcher.extract_and_match(temp_path)
            
            if not results:
                return jsonify({'error': 'OCR 결과를 추출할 수 없습니다'}), 400
            
            # 구조화된 결과 생성
            structured = matcher.get_structured_results(results)
            
            # 통계 계산
            total_fields = len(results)
            detected_fields = sum(1 for v in results.values() if v is not None and v != "미검출")
            detection_rate = (detected_fields / total_fields * 100) if total_fields > 0 else 0
            
            response = {
                'success': True,
                'data': {
                    'raw': results,
                    'structured': structured
                },
                'stats': {
                    'total_fields': total_fields,
                    'detected_fields': detected_fields,
                    'detection_rate': round(detection_rate, 1)
                },
                'options': {
                    'auto_perspective': auto_perspective,
                    'skew_threshold': skew_threshold
                }
            }
            
            return jsonify(response)
        
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error: {error_detail}", file=sys.stderr)
        
        return jsonify({
            'error': str(e),
            'detail': error_detail if app.debug else None
        }), 500


@app.route('/api/download', methods=['POST'])
def download_results():
    """결과를 JSON 파일로 다운로드"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '데이터가 없습니다'}), 400
        
        # 임시 JSON 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            temp_path = f.name
        
        try:
            return send_file(
                temp_path,
                mimetype='application/json',
                as_attachment=True,
                download_name='inbody_result.json'
            )
        finally:
            # 파일 전송 후 삭제
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """파일 크기 초과 에러 핸들러"""
    return jsonify({'error': f'파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 가능합니다'}), 413


if __name__ == '__main__':
    print("=" * 60)
    print("InBody OCR Web Server")
    print("=" * 60)
    print(f"📁 업로드 폴더: {UPLOAD_FOLDER}")
    print(f"📏 최대 파일 크기: {MAX_FILE_SIZE // (1024*1024)}MB")
    print(f"📝 허용 확장자: {', '.join(ALLOWED_EXTENSIONS)}")
    print("=" * 60)
    print("\n서버 시작 중...")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )