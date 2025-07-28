#run_both.py
import subprocess
import sys

def run_python(file):
    return subprocess.Popen([sys.executable, file])

if __name__ == "__main__":
    # 필요에 따라 파일 경로를 수정하세요
    p1 = run_python("app.py")
    p2 = run_python("fetch_all_users_loop.py")
    try:
        # 두 프로세스가 종료될 때까지 대기
        p1.wait()
        p2.wait()
    except KeyboardInterrupt:
        print("종료 요청. 프로세스 종료 중...")
        p1.terminate()
        p2.terminate()
