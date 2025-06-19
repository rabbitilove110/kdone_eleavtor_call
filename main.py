from flask import Flask, request, jsonify
from KDOne.api import KDOneAPI
from KDOne.models.device import DeviceType, StatusType
import threading
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# KDOne 유저정보
KDONE_USERNAME = 'ID'
KDONE_PASSWORD = 'PW'
KDONE_COMPLEX_ID = 'complex_ID'

TOKEN_FILE = 'kdone_token.json'

kd_one = None
is_authenticated = False
auth_lock = threading.Lock()

def authenticate_kdone():
    global kd_one, is_authenticated
    with auth_lock:
        if is_authenticated and kd_one is not None:
            print("KDOneAPI가 이미 인증되었어요.")
            return True

        kd_one = KDOneAPI(username=KDONE_USERNAME, password=KDONE_PASSWORD)
        token_data_loaded = None
        
        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data_loaded = json.load(f)

            expire_date_str = token_data_loaded.get('expire_date')
            
            if expire_date_str:
                loaded_expire_date = datetime.fromisoformat(expire_date_str)
                if loaded_expire_date < datetime.now() - timedelta(minutes=5):
                    print("저장된 토큰이 만료되었거나, 올바르지 않아요.\n재 인증을 진행합니다.")
                    token_data_loaded = None
            else:
                token_data_loaded = None

        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            print(f"저장된 토큰 로드 실패: {e}.")
            token_data_loaded = None

        try:
            if token_data_loaded:
                kd_one.access_token = token_data_loaded.get('access_token')
                kd_one.refresh_token = token_data_loaded.get('refresh_token')
                
                print("유효성 검사 중")
                kd_one.get_complexes() 

                is_authenticated = True
                print("저장된 토큰으로 KDOneAPI 인증 성공!")
                return True

            else:
                print("유효한 토큰이 없어요.\n 재인증을 통한 새로운 토큰을 발급할게요!")
                print("단지 정보를 불러오는 중이에요.")

                kd_one.get_complexes()
                print(f"ID: {KDONE_USERNAME}, 아파트 ID: {KDONE_COMPLEX_ID}로 로그인 시도 중...")
                kd_one.login(complex_id=KDONE_COMPLEX_ID)
                print("월패드 인증번호를 요청했어요!")

                certify_number = input('월패드에 전송된 인증번호를 입력해주세요: ')
                kd_one.certify(certify_number=certify_number)
                print("인증에 성공했어요. 토큰 발급 중...")
                
                token_response = kd_one.get_token()
                access_token_val = None
                refresh_token_val = None
                expires_in_seconds = None

                if isinstance(token_response, dict) and "Resources" in token_response:
                    resources = token_response["Resources"]
                    if resources and "Oauth" in resources[0]:
                        oauth_data = resources[0]["Oauth"]
                        access_token_val = oauth_data.get('Access_Token')
                        refresh_token_val = oauth_data.get('Refresh_Token')
                        expires_in_seconds = oauth_data.get('Expires_In')
                
                expire_date_obj = None
                if expires_in_seconds is not None:
                    expire_date_obj = datetime.now() + timedelta(seconds=expires_in_seconds)

                token_data_to_save = {
                    'access_token': access_token_val,
                    'refresh_token': refresh_token_val,
                    'expire_date': expire_date_obj.isoformat() if isinstance(expire_date_obj, datetime) else None
                }
                print(f"토큰 저장 데이터를 불러왔어요: {token_data_to_save}")

                if token_data_to_save.get('access_token'):
                    try:
                        with open(TOKEN_FILE, 'w') as f:
                            json.dump(token_data_to_save, f, indent=4)
                        print(f"새로운 토큰을 '{TOKEN_FILE}'에 성공적으로 저장했습니다.")
                    except IOError as io_e:
                        print(f"토큰 파일 저장을 실패했어요! 권한 문제인거 같아요: {io_e}")
                    except TypeError as type_e:
                        print(f"JSON으로 변환이 안되는 정보가 포함되어 있어요: {type_e}")
                    except Exception as gen_e:
                        print(f"알수없는 문제가 발생했어요! 잠시후 다시 시도하세요: {gen_e}")
                else:
                    print("액세스 토큰이 유효하지 않거나 받아오지 못했어요. 다시 시도해주세요.")
                
                is_authenticated = True
                print("KDOneAPI 인증 성공!")
                return True

        except Exception as e:
            print(f"인증 도중 오류가 발생했어요: {e}")
            is_authenticated = False
            kd_one = None 
            return False

def check_authentication():
    global is_authenticated, kd_one
    if not is_authenticated or kd_one is None:
        print("KDOneAPI가 인증되지 않았습니다. 서버를 재시작하여 인증을 완료해주세요.")
        return False
    return True

# --- 엘리베이터 호출 ---
def perform_elevator_call():
    if not check_authentication():
        return {"status": "error", "message": "KDOneAPI 인증이 필요합니다. 서버를 재시작하여 월패드 인증을 완료해주세요."}, 401
    try:
        print("엘리베이터 호출 시도중")
        kd_one.call_elevator()
        print("엘리베이터 호출 요청 성공!")
        return {"status": "success", "message": "엘리베이터 호출 요청이 성공적으로 전송되었습니다."}, 200
    except Exception as e:
        print(f"엘리베이터 호출 중 오류 발생: {e}")
        error_msg_detail = str(e)
        if "Unauthorized" in error_msg_detail or "Token" in error_msg_detail:
             is_authenticated = False
             return {"status": "error", "message": f"인증 토큰이 만료되었거나 유효하지 않습니다. 서버를 재시작하여 다시 인증해주세요. 오류: {error_msg_detail}"}, 401
        return {"status": "error", "message": f"엘리베이터 호출 실패: {error_msg_detail}"}, 500

@app.route('/call_elevator', methods=['POST'])
def call_elevator_post():
    response, status_code = perform_elevator_call()
    return jsonify(response), status_code

@app.route('/call_elevator_get', methods=['GET'])
def call_elevator_get():
    response, status_code = perform_elevator_call()
    return jsonify(response), status_code

@app.route('/status', methods=['GET'])
def get_server_status():
    status_message = "KDOne 엘리베이터 호출 서버가 실행중이에요."
    auth_status = "인증되지 않음"
    if is_authenticated:
        auth_status = "인증됨"
    return jsonify({
        "server_status": status_message,
        "kdone_api_auth_status": auth_status,
        "authenticated": is_authenticated
    }), 200

@app.route('/')
def home():
    return "KDOne 엘리베이터 호출 서버가 실행중이에요."

if __name__ == '__main__':
    print("KDOne 엘리베이터 호출 서버 인증을 시작합니다.")
    if authenticate_kdone():
        print("\nKDOneAPI 인증이 완료되었습니다. Flask 서버를 시작합니다.")
        app.run(host='0.0.0.0', port=5000)
    else:
        print("\nKDOneAPI 인증에 실패하여 Flask 서버를 시작할 수 없습니다. 다시 시도해주세요.")