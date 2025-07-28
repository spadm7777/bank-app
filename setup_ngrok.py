import os
import subprocess
import sys

def setup_ngrok():
    print("🚀 ngrok 설정 도우미")
    print("=" * 50)
    
    # ngrok 다운로드 확인
    ngrok_path = "ngrok.exe"
    if not os.path.exists(ngrok_path):
        print("📥 ngrok 다운로드 중...")
        print("1. https://ngrok.com/download 에서 ngrok 다운로드")
        print("2. 압축 해제 후 ngrok.exe를 이 폴더에 복사")
        print("3. ngrok 계정 가입 후 authtoken 설정")
        return False
    
    print("✅ ngrok.exe 발견됨")
    
    # authtoken 설정 확인
    try:
        result = subprocess.run([ngrok_path, "config", "check"], 
                              capture_output=True, text=True)
        if "authtoken" in result.stdout:
            print("✅ ngrok authtoken 설정됨")
        else:
            print("⚠️ ngrok authtoken 설정 필요")
            print("1. https://dashboard.ngrok.com/get-started/your-authtoken")
            print("2. ngrok config add-authtoken [YOUR_TOKEN]")
            return False
    except:
        print("❌ ngrok 실행 오류")
        return False
    
    return True

def start_ngrok():
    print("\n🌐 ngrok 터널 시작...")
    print("외부 접속 URL이 생성됩니다.")
    print("Ctrl+C로 중지")
    
    try:
        subprocess.run([ngrok_path, "http", "5000"])
    except KeyboardInterrupt:
        print("\n⏹️ ngrok 중지됨")

if __name__ == "__main__":
    if setup_ngrok():
        start_ngrok()
    else:
        print("\n📋 ngrok 설정 완료 후 다시 실행하세요.") 