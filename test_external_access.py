import socket

def test_external_access():
    print("🔍 외부 접속 테스트...")
    
    # 로컬 IP 확인
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"🏠 로컬 IP: {local_ip}")
    
    print("⚠️ 외부 IP 확인은 인터넷에서 '내 IP 확인' 검색으로 확인하세요")
    
    # 포트 확인
    port = 5000
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:
        print(f"✅ 포트 {port} 열림")
    else:
        print(f"❌ 포트 {port} 닫힘")
    
    print(f"\n📋 접속 방법:")
    print(f"   1. 로컬 접속: http://localhost:{port}")
    print(f"   2. 내부망 접속: http://{local_ip}:{port}")
    print(f"   3. 외부 접속: http://[외부IP]:{port} (라우터 포트포워딩 필요)")
    
    print(f"\n🔧 라우터 설정:")
    print(f"   - 라우터 관리자 페이지 접속")
    print(f"   - 포트포워딩 설정: 외부포트 5000 → 내부포트 5000")
    print(f"   - 대상 IP: {local_ip}")

if __name__ == "__main__":
    test_external_access() 