import socket
import urllib.request
import json

def get_external_ip():
    """외부 IP 주소 확인"""
    try:
        with urllib.request.urlopen('https://api.ipify.org') as response:
            return response.read().decode('utf-8')
    except:
        return None

def test_port_access(host, port):
    """포트 접근 가능 여부 테스트"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def main():
    print("🌐 외부 접속 테스트 도구")
    print("=" * 50)
    
    # 외부 IP 확인
    external_ip = get_external_ip()
    if external_ip:
        print(f"🌍 외부 IP: {external_ip}")
        
        # 포트 접근 테스트
        if test_port_access(external_ip, 5000):
            print("✅ 외부에서 포트 5000 접근 가능")
            print(f"🔗 접속 URL: http://{external_ip}:5000")
        else:
            print("❌ 외부에서 포트 5000 접근 불가")
            print("💡 라우터 포트포워딩 설정이 필요합니다")
    else:
        print("⚠️ 외부 IP 확인 실패")
    
    print("\n📋 외부 접속 방법:")
    print("1. 라우터 포트포워딩: router_setup_guide.txt 참조")
    print("2. ngrok 사용: python setup_ngrok.py")
    print("3. 클라우드 배포: Heroku, AWS, GCP 등")

if __name__ == "__main__":
    main() 