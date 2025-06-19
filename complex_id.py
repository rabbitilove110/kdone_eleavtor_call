from KDOne.api import KDOneAPI

# KDOne 유저 정보
KDONE_USERNAME = 'ID'
KDONE_PASSWORD = 'PW'

try:
    kd_one = KDOneAPI(username=KDONE_USERNAME, password=KDONE_PASSWORD)

    print("모든 단지 정보를 불러오고 있어요. 기다려주세요.")
    complexes = kd_one.get_complexes()

    if complexes:
        print("\n===== 불러온 단지 정보 =====")
        for i, comp in enumerate(complexes):
            print(f"[{i+1}]")
            print(f"  단지 이름: {comp.name}")
            print(f"  단지 ID: {comp.id}")
            print(f"  주소: {comp.address}")
            print("-" * 20)
        print("\n원하는 단지를 선택해서 이용하세요.")
    else:
        print("단지정보를 불러오지 못했어요.")

except Exception as e:
    print(f"오류가 발생했어요: {e}")
    print("아이디 또는 비밀번호가 잘못되었거나, 네트워크 문제일 수 있어요.")