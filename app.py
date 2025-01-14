import subprocess
import threading
import random
import time
from flask import Flask, render_template, Response, send_file, request, redirect, url_for, session, flash, jsonify
from mutagen import File
from PIL import Image
import io
import copy
import os
import urllib.parse
from multiprocessing import Queue, Process
import concurrent.futures
import sys
import argparse
app = Flask(__name__)
app.secret_key = "qwyueyqwhuidhuwi@#&(*&!&@#*(HNCDLKJNCLK:SS!@#(*&(*!%*!@))))"  # 세션을 사용하기 위한 비밀 키 설정
# 스레드 풀 생성 (최대 10개의 스레드 사용)
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
# 현재 접속자 수를 추적하기 위한 변수와 락 설정
current_users = 0
user_lock = threading.Lock()

# 사용자 데이터
users = {
    "user": "12345"  # 사용자 이름과 비밀번호
}

# 차단된 사용자의 접속 시간을 저장하는 딕셔너리
blocked_users = {}
# 로그인 실패 횟수를 저장하는 딕셔너리
failed_login_attempts = {}

# Heartbeat를 위한 마지막 핑 시간을 저장하는 딕셔너리
last_ping_time = {}

# 청크 크기 설정
CHUNK_SIZE = 512# 64KB 단위로 데이터를 전송

def is_safe_path(base_path, user_path):
    """
    주어진 경로가 허용된 디렉토리 내부에 있는지 확인합니다.
    """
    abs_base = os.path.abspath(base_path)
    abs_path = os.path.abspath(os.path.join(base_path, user_path))
    return abs_path.startswith(abs_base)

# 오디오 파일 목록을 추출하는 함수
def extract_audio_files(file_list_path):
    audio_files = []
    with open(file_list_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if "*file*" in line:
                file_path = line.split("*file*")[1]
                absolute_file_path = os.path.abspath(file_path)
                
                # UTF-8로 인코딩된 경로를 사용하여 처리
                encoded_path = absolute_file_path.encode('utf-8').decode('utf-8')

                # 다양한 확장자에 따른 처리
                if encoded_path.endswith(".flac"):
                    cleaned_file_name = os.path.basename(encoded_path)[:-5]  # '.flac' 제거
                elif encoded_path.endswith(".wav"):
                    cleaned_file_name = os.path.basename(encoded_path)[:-4]  # '.wav' 제거
                elif encoded_path.endswith(".mp3"):
                    cleaned_file_name = os.path.basename(encoded_path)[:-4]  # '.mp3' 제거
                elif encoded_path.endswith(".aiff"):
                    cleaned_file_name = os.path.basename(encoded_path)[:-5]  # '.aiff' 제거
                elif encoded_path.endswith(".dsf") or encoded_path.endswith(".dff"):
                    cleaned_file_name = os.path.basename(encoded_path)[:-4]  # '.dsf' 또는 '.dff' 제거
                else:
                    cleaned_file_name = os.path.basename(encoded_path)  # 다른 확장자 또는 확장자 없는 파일은 그대로 유지
                
                # 파일 정보를 추가
                audio_files.append({"path": encoded_path, "name": cleaned_file_name})
    return audio_files



# os.path.abspath 함수로 경로를 OS에 맞게 수정
file_list_path = os.path.abspath("./audio_file_list.txt");
audio_files = extract_audio_files(file_list_path)
# 서버에서 재생 목록을 랜덤하게 섞음
shuffled_audio_files = copy.deepcopy(audio_files)
random.shuffle(shuffled_audio_files)

# Heartbeat 기능을 구현하여 주기적으로 클라이언트 연결 상태를 확인
def heartbeat_checker():
    while True:
        current_time = time.time()
        with user_lock:
            for user, last_ping in list(last_ping_time.items()):
                if current_time - last_ping > 30:  # 30초 동안 응답이 없는 경우 연결 끊김으로 간주
                    print(f"Client {user} disconnected due to inactivity")
                    del last_ping_time[user]
        threading.Event().wait(20)  # 20초마다 체크
# Heartbeat 엔드포인트
@app.route("/ping", methods=["POST"])
def ping():
    username = session.get("username")
    if username:
        with user_lock:
            last_ping_time[username] = time.time()
        return jsonify({"status": "alive"}), 200
    return jsonify({"status": "unauthorized"}), 401

# 앨범 커버 추출 함수
def extract_album_cover(file_path):
    try:
        audio = File(file_path)
        if audio is None:
            print(f"지원되지 않는 파일 형식: {file_path}")
            return None
        
        if "APIC:" in audio.tags:
            album_cover = audio.tags["APIC:"].data
        elif "covr" in audio:
            album_cover = audio["covr"][0]
        elif hasattr(audio, "pictures") and len(audio.pictures) > 0:
            album_cover = audio.pictures[0].data
        else:
            print("앨범 커버를 찾을 수 없습니다2.")
            image = Image.open(r".\none.png")
            image_byte_array = image.save(io.BytesIO(), format="PNG")
            image.save(image_byte_array, format="PNG")
            image_byte_array.seek(0)
            return image_byte_array

        image = Image.open(io.BytesIO(album_cover))
        image_byte_array = io.BytesIO()
        image.save(image_byte_array, format="PNG")
        image_byte_array.seek(0)
        return image_byte_array

    except Exception as e:
        print(f"앨범 커버를 추출할 수 없습니다: {e}")
    return None 

@app.route("/public/none")
def error_album_cover():
    image = Image.open(r".\none.png")
    image_byte_array = image.save(io.BytesIO(), format="PNG")
    image.save(image_byte_array, format="PNG")
    image_byte_array.seek(0)
    print("앨범 커버를 찾을 수 없습니다.")
    return image_byte_array

# 앨범 커버를 제공하는 라우트
@app.route("/cover/<filename>")
def get_album_cover(filename):
    file_info = next((f for f in shuffled_audio_files if os.path.basename(f["path"]) == filename), None)
    if file_info and os.path.exists(file_info["path"]):
        image = extract_album_cover(file_info["path"])
        if image:
            return send_file(image, mimetype="image/png")
    return "No cover available", 404
    
@app.route("/")
def index():
    global current_users
    with user_lock:
        current_users += 1
        print(f"현재 접속자 수: {current_users}")  # 접속자 수를 터미널에 출력

    # 접속 차단 확인
    username = session.get("username")
    
    # 차단된 사용자 처리
    if username in blocked_users:
        block_time = blocked_users[username]
        if time.time() - block_time < 30:  # 30초 동안 차단
            return "접속이 차단되었습니다. 잠시 후 다시 시도해주세요.", 403  # 403 Forbidden
        else:
            # 30초가 경과하면 차단 해제 및 실패 횟수 초기화
            del blocked_users[username]
            failed_login_attempts[username] = 0  # 초기화

    if "username" in session:
        return render_template("index.html", audio_files=shuffled_audio_files)
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # 로그인 실패 횟수 확인 및 업데이트
        if username not in failed_login_attempts:
            failed_login_attempts[username] = 0
        
        if username in users and users[username] == password:
            session["username"] = username  # 세션에 사용자 정보 저장
            flash("로그인 성공!")
            # 실패 횟수 초기화
            failed_login_attempts[username] = 0
            return redirect(url_for("index"))
        else:
            flash("사용자 이름 또는 비밀번호가 잘못되었습니다.")
            # 로그인 실패 시 실패 횟수 증가
            failed_login_attempts[username] += 1
            
            # 5회 실패 시 차단 처리
            if failed_login_attempts[username] >= 5:
                blocked_users[username] = time.time()  # 현재 시간을 차단 시간으로 저장
                flash("5회 로그인 실패로 인해 접속이 차단되었습니다. 30초 후에 다시 시도해 주세요.")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)  # 세션에서 사용자 정보 제거
    flash("로그아웃되었습니다.")
    return redirect(url_for("login"))

#def sanitize_path(file_path):
    # 경로 내의 공백이나 특수문자를 URL 인코딩 방식으로 변환
#    return urllib.parse.quote(file_path)
# 오디오 스트리밍
# 현재 실행 중인 ffmpeg 프로세스를 추적하기 위한 전역 변수
current_process = None

import threading
import time

max_processes = sys.maxsize # 최대 실행 가능한 프로세스 수
process_list = []  # 프로세스 목록: [(process, last_access_time)]

process_list_lock = threading.Lock()
stop_event = threading.Event()

# 현재 실행 중인 프로세스 관리 함수
def manage_process_list():
    global process_list
    with process_list_lock:  # 락을 사용하여 동시성 문제 방지
        process_list = [(proc, last_access) for proc, last_access in process_list if proc.poll() is None] # 종료되지 않은 프로세스만 남김
        #위 코드의 과정은 다음과 같습니다. process_list의 각 요소를 순회하면서 프로세스의 poll() 메서드를 사용하여 프로세스가 종료되었는지 확인합니다. 종료되지 않은 프로세스만 남기고 나머지는 제거합니다.
        #proces_list에 프로세스가 들어가는 내용은 어떤 함수인지 
    print(f"현재 실행 중인 프로세스 수: {len(process_list)}")

def terminate_inactive_processes_with_duration():
    """
    비활성 프로세스 종료 스레드 함수 (재생 시간 기준 추가).
    """
    global process_list
    with app.app_context():  # Flask 애플리케이션 컨텍스트 설정
        while not stop_event.is_set():  # stop_event가 설정되지 않은 동안 반복
            current_time = time.time()
            with process_list_lock:
                for proc, last_access in process_list[:]:
                    try:
                        # 프로세스 파일의 경로를 찾음
                        proc_info = next((f for f in shuffled_audio_files if proc.args and f["path"] in proc.args), None)
                        if not proc_info:
                            continue

                        file_duration = get_audio_duration(proc_info["path"])
                        # file_duration 값 검증
                        if file_duration is None or not isinstance(file_duration, (float, int)):

                            continue

                        # 프로세스가 재생 시간 + 0.5초를 초과했는지 확인
                        if current_time - last_access >= file_duration + 0.5 and proc.poll() is None:
                            proc.terminate()
                            try:
                                proc.wait(timeout=1)  # 1초 대기 후 종료 확인
                                if proc.poll() is None:  # 여전히 종료되지 않았다면
                                    proc.kill()  # 강제 종료
                                    proc.wait()  # 강제 종료 후 대기
                                print(f"프로세스 종료됨. PID: {proc.pid}, 종료 코드: {proc.returncode}")
                            except subprocess.TimeoutExpired:
                                print(f"프로세스 {proc.pid} 종료 대기 시간 초과. 강제 종료 시도.")
                                proc.kill()  # 강제 종료 시도
                                proc.wait()  # 강제 종료 후 대기
                            finally:
                                # 정상적으로 종료된 경우 리스트에서 제거
                                process_list.remove((proc, last_access))
                    except Exception as e:
                        print(f"프로세스 {proc.pid} 종료 중 오류 발생: {e}")
            time.sleep(0.5)  # 0.5초마다 반복


def get_audio_duration(file_path):
    """
    주어진 음원 파일의 재생 시간을 초 단위로 반환.
    """
    try:
        audio = File(file_path)
        if audio and audio.info:
            return audio.info.length
    except Exception as e:
        print(f"오류 발생: {e}")
    return audio.info.length

# 오디오 재생 시간 엔드포인트 추가
@app.route("/audio/duration", methods=["POST"])
def post_audio_duration():
    file_path = request.form.get("file_path")
    if not file_path:
        return jsonify({"error": "No file path provided"}), 400

    file_duration = get_audio_duration(file_path)
    if file_duration is None:
        return jsonify({"error": "Could not retrieve duration"}), 500

    return jsonify({"duration": file_duration})



# 비활성 프로세스 종료 스레드 시작
cleanup_thread = threading.Thread(target=terminate_inactive_processes_with_duration, daemon=True)
cleanup_thread.start()


@app.route("/audio/<filename>")
def stream_audio(filename):
    filter_string = ''  # 필터가 없을 때 기본값은 빈 문자열

    selected_effects = request.args.get('effects', '')

    # 음장 효과 필터 설정
    filter_string = ''  # 필터가 없을 때 기본값은 빈 문자열
    
    if 'echo' in selected_effects:
        filter_string += 'aecho=0.8:0.9:1000:0.3'  # 에코 필터 추가


    manage_process_list()  # 현재 실행 중인 프로세스 관리
    if len(process_list) >= max_processes:
        return "Maximum number of processes running. Try again later.", 429  # Too many requests
    
    # 파일 정보 찾기
    file_info = next((f for f in shuffled_audio_files if os.path.basename(f["path"]) == filename), None)
    if file_info and os.path.exists(file_info["path"]):
        print(f"Streaming file: {file_info['path']}")
        # 파일의 길이 출력
        print(f"File duration: {get_audio_duration(file_info['path'])} seconds")
        def generate():
            file_path = os.path.abspath(file_info["path"])
            # 파일 확장자 추출
            file_extension = os.path.splitext(file_path)[1].lower()
            # 확장자에 따른 FFmpeg 명령어 설정
            if file_extension == '.aiff':
                command = ['ffmpeg', '-i', file_path, '-map', '0:a', '-f', 'flac', '-c:a', 'flac', '-sample_fmt', 's32', '-threads', '4']
            elif file_extension in ['.dsf', '.dff']:
                command = ['ffmpeg', '-i', file_path, '-map', '0:a', '-f', 'flac', '-ar', '352800', '-c:a', 'flac', '-sample_fmt', 's32', '-threads', '4']
            elif file_extension == '.wav':
                command = ['ffmpeg', '-i', file_path, '-map', '0:a', '-f', 'flac', '-c:a', 'flac', '-threads', '4']
            elif file_extension == '.flac':
                command = ['ffmpeg', '-i', file_path, '-map', '0:a', '-f', 'flac', '-c:a', 'flac', '-threads', '4']
            elif file_extension == '.mp3':
                command = ['ffmpeg', '-i', file_path, '-map', '0:a', '-f', 'flac', '-c:a', 'flac', '-sample_fmt', 's16', '-threads', '4']
                        # 음장 효과 필터가 있을 경우 명령어에 필터 추가
            else:
                command = ['ffmpeg', '-i', file_path, '-map', '0:a', '-f', 'flac', '-c:a', 'flac', '-threads', '4']
            # 음장 효과 필터가 있을 경우 명령어에 필터 추가
            if filter_string:
                command.extend(['-af', filter_string])

            command.append('-')  # FFmpeg 출력 설정을 파이프로 처리
                
            # FFmpeg 프로세스를 stdout으로 실행
            current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process_list.append((current_process, time.time()))  # 프로세스 추가 및 시간 기록
            try:
                while True: # 데이터를 전송할 때마다 last_access 갱신
                    chunk = current_process.stdout.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    yield chunk

                    # 데이터를 전송할 때마다 last_access 갱신
                    for i, (proc, last_access) in enumerate(process_list):
                        if proc == current_process:
                            process_list[i] = (proc, time.time())  # 데이터 전송 중이므로 갱신

                remaining_data = current_process.stdout.read()
                while remaining_data:
                    yield remaining_data
                    remaining_data = current_process.stdout.read()

            except Exception as e:
                print(f"Error while streaming: {e}")

            finally:
                current_process.stdout.close()
                current_process.wait()

                error = current_process.stderr.read().decode(errors="ignore")
                if current_process.returncode != 0:
                    print(f"FFmpeg error (Exit Code {current_process.returncode}): {error}")
                manage_process_list()

        return Response(generate(), mimetype="audio/flac")


@app.route("/audio/duration/<filename>", methods=["GET"])
def get_duration(filename):
    """
    특정 음원 파일의 총 길이를 반환하는 API.
    """
    # 파일 정보 찾기
    file_info = next((f for f in shuffled_audio_files if os.path.basename(f["path"]) == filename), None)

    if not file_info or not os.path.exists(file_info["path"]):
        return jsonify({"error": "File not found"}), 404

    # 음원 파일 길이 가져오기
    file_duration = get_audio_duration(file_info["path"])
    if file_duration is None:
        return jsonify({"error": "Could not retrieve duration"}), 500

    # 길이를 JSON 형식으로 반환
    return jsonify({"filename": filename, "duration": file_duration})


    return "File not found", 404
app.config['SESSION_COOKIE_SECURE'] = False # HTTPS에서만 세션 쿠키 전송
app.config['SESSION_COOKIE_HTTPONLY'] = True # JavaScript에서 세션 쿠키 접근 불가
#이렇게 설정하면 세션 쿠키가 HTTPS 프로토콜을 사용하는 경우에만 전송되며, JavaScript를 통해 세션 쿠키에 접근할 수 없습니다.
#보안적으로는 좋고, 음악 재생에는 영향을 주지 않습니다.

# see: https://www.geeksforgeeks.org/command-line-arguments-in-python/
parser = argparse.ArgumentParser()

# `--debug` 추가 시 args.debug == True
parser.add_argument("--debug", action='store_true', help = "Debug Mode")

args = parser.parse_args()

if __name__ == "__main__":
    heartbeat_thread = threading.Thread(target=heartbeat_checker)
    heartbeat_thread.start()
    app.run(host="0.0.0.0", debug=args.debug, threaded=True, port=8000)
