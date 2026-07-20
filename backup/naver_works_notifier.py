import subprocess
import os
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def send_naver_works_message(api_base_url, secret_key, bot_id, target_email, report_path):
    if not api_base_url:
        print("[오류] NAVER_WORKS_API_URL이 설정되지 않아 네이버웍스 메시지를 발송할 수 없습니다.")
        return False

    java_executable = os.path.join(BASE_DIR, "../jdk-17.0.12+7", "Contents", "Home", "bin", "java")
    if not os.path.exists(java_executable):
        java_executable = "java"
        
    # works-api-client jar 동적 탐색 (with-dependencies 우선)
    jar_files = glob.glob(os.path.join(BASE_DIR, "works-api-client*.jar"))
    if not jar_files:
        print("[오류] works-api-client JAR 파일을 찾을 수 없습니다.")
        return False
        
    # jar-with-dependencies 가 있으면 우선 사용
    jar_path = next((j for j in jar_files if "dependencies" in j), jar_files[0])
    classpath = f"{jar_path}{os.pathsep}."
    
    # 1. Compile the Java file if NaverWorksSender.class does not exist
    if not os.path.exists(os.path.join(BASE_DIR, "NaverWorksSender.class")):
        javac_executable = os.path.join(BASE_DIR, "../jdk-17.0.12+7", "Contents", "Home", "bin", "javac")
        if not os.path.exists(javac_executable):
            javac_executable = "javac"
        compile_cmd = [javac_executable, "-cp", classpath, "NaverWorksSender.java"]
        print("컴파일 시작:", " ".join(compile_cmd))
        try:
            compile_res = subprocess.run(compile_cmd, cwd=BASE_DIR, capture_output=True, text=True)
            if compile_res.returncode != 0:
                print("[오류] NaverWorksSender.java 컴파일 실패:", compile_res.stderr)
                return False
        except Exception as e:
            print("[오류] 컴파일러 실행 실패:", e)
            return False

    # 2. Run the Java class
    cmd = [
        java_executable,
        "-cp", classpath,
        "NaverWorksSender",
        api_base_url,
        secret_key,
        str(bot_id),
        target_email,
        f"file://{os.path.abspath(report_path)}"
    ]
    
    print("메시지 발송 요청 중...")
    try:
        res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
        if res.returncode == 0:
            print("[성공] 네이버웍스 메시지 발송 완료")
            return True
        else:
            print("[실패] 네이버웍스 메시지 발송 오류:", res.stderr, res.stdout)
            return False
    except Exception as e:
        print("[실패] 래퍼 실행 중 오류 발생:", e)
        return False
