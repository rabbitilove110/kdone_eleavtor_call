# kdone_eleavtor_call
soulee-dev님이 만드신 KDOne 모듈을 통해서 엘리베이터 호출 API를 만들었습니다.
Gemini와 일부 기능은 같이 만들었습니다.

KDOne 유저정보 수정해서 쓰시면됩니다.

스마트 싱스 연동은 IFTTT나 엣지드라이버 이용하시면 됩니다.

## 사용법
1. 파이썬 설치
2. complex_id.py 세팅후 실행
3. main.py 세팅후 실행
4. 월패드 인증
5. GET, POST 나누어져 있습니다. (https://localhost:5000/call_eleavtor_get, https://localhost:5000/call_elevator)
6. 요긴하게 잘 사용하시면 됩니다.

## 주의사항!!
미리 아파트 정보를 경동원 홈 네트워크 앱에서 꼭 설정하고 사용하세요.
해당 코드는 동/호수 입력기능을 지원하지 않습니다.
