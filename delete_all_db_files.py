
import os

base_path = "."
deleted_files = []

for root, dirs, files in os.walk(base_path):
    for file in files:
        if file.endswith(".db"):
            full_path = os.path.join(root, file)
            try:
                os.remove(full_path)
                deleted_files.append(full_path)
                print(f"🗑️ 삭제됨: {full_path}")
            except Exception as e:
                print(f"⚠️ 삭제 실패: {full_path} → {e}")

print(f"✅ 총 {len(deleted_files)}개 DB 파일 삭제 완료.")
