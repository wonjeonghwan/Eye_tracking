import win32pipe
import win32file
import struct
import threading
import time
from eye_tracking import run_eye_tracking
from calibration import run_full_calibration

# NotifyMessage 포맷 정의 (quiz_id, setting_start, start, end)
class NotifyMessage:
    STRUCT_FORMAT = '<BBBB'

PIPE_NAME = r"\\.\pipe\unreal_pipe"

state = {
    "calibrating": False,
    "tracking": False
}

def start_pipe_server(stop_event=None, pipe_ready_event=None):
    print(f"📡 [Pipe] Named Pipe 서버 시작: {PIPE_NAME}")
    while True:
        try:
            pipe = win32pipe.CreateNamedPipe(
                PIPE_NAME,
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
                1, 65536, 65536, 0, None
            )
            win32pipe.ConnectNamedPipe(pipe, None)
            print("🔗 [Pipe] 클라이언트 연결 완료")
            if pipe_ready_event:
                pipe_ready_event.set()
            handle_client(pipe, stop_event)
        except Exception as e:
            print(f"❌ [Pipe] 연결 실패: {e}")
            time.sleep(1)
            continue


def handle_client(pipe, stop_event=None):
    print("👂 [Pipe] 클라이언트 통신 시작")
    buffer = b""
    screen_w, screen_h = 2880, 1800

    while stop_event is None or not stop_event.is_set():
        try:
            result, data = win32file.ReadFile(pipe, 1024)
            buffer += data

            while len(buffer) >= 4:  # 최소 NotifyMessage 크기
                header = struct.unpack(NotifyMessage.STRUCT_FORMAT, buffer[:4])
                quiz_id, setting_start, start, end = header

                if setting_start not in (0, 1) or start not in (0, 1) or end not in (0, 1):
                    print(f"⚠️ 잘못된 데이터 무시: {header}")
                    buffer = buffer[4:]
                    continue

                print(f"📩 수신 - QuizID:{quiz_id} SettingStart:{setting_start} Start:{start} End:{end}")
                buffer = buffer[4:]

                if setting_start == 1:
                    print("🛠️ 칼리브레이션 시작")
                    state["calibrating"] = True
                    state["tracking"] = False
                    run_full_calibration(screen_w, screen_h)

                elif start == 1:
                    print("🚀 미션 시작 (좌표 전송)")
                    state["tracking"] = True
                    state["calibrating"] = False
                    # 새로운 stop_event 인스턴스 생성
                    local_stop_event = threading.Event()
                    state["local_stop_event"] = local_stop_event
                    run_eye_tracking(screen_w, screen_h, pipe=pipe, stop_event=local_stop_event)

                elif end == 1:
                    print("🛑 미션 종료 (대기 상태)")
                    state["tracking"] = False
                    if "local_stop_event" in state:
                        state["local_stop_event"].set()

        except Exception as e:
            print(f"❗ 통신 오류: {e}")
            break

    print("📴 파이프 통신 종료")
    win32file.CloseHandle(pipe)
