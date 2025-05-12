# pipe_server.py
import win32pipe
import win32file
import struct
import threading
import win32security
import pywintypes
from eye_tracking import run_relative_eye_tracking

PIPE_RECV = r"\\.\pipe\unreal_to_python"  # Unreal → Python 제어 메시지 수신

pipe_connected_event = threading.Event()

class NotifyMessage:
    STRUCT_FORMAT = '<BBBB'

def handle_client(pipe):
    buffer = b""
    screen_w, screen_h = 2880, 1800
    local_stop_event = threading.Event()

    while True:
        try:
            _, data = win32file.ReadFile(pipe, 1024)
            buffer += data

            while len(buffer) >= 4:
                header = struct.unpack(NotifyMessage.STRUCT_FORMAT, buffer[:4])
                quiz_id, setting_start, start, end = header
                buffer = buffer[4:]

                print(f"📉 수신 - QuizID:{quiz_id} SettingStart:{setting_start} Start:{start} End:{end}")

                if start == 1:
                    print("🚀 미션 시작")
                    local_stop_event.clear()
                    tracking_thread = threading.Thread(
                        target=run_relative_eye_tracking,
                        args=(screen_w, screen_h),
                        kwargs={"stop_event": local_stop_event}  # pipe 제거
                    )
                    tracking_thread.start()

                elif end == 1:
                    print("🛑 미션 종료")
                    local_stop_event.set()

        except Exception as e:
            print(f"❌ 통신 오류: {e}")
            break

    win32file.CloseHandle(pipe)
    print("📴 파이프 종료")

def get_open_security_attributes():
    sd = win32security.SECURITY_DESCRIPTOR()
    sd.Initialize()
    sd.SetSecurityDescriptorDacl(1, None, 0)

    sa = pywintypes.SECURITY_ATTRIBUTES()  # ✅ 올바른 클래스
    sa.SECURITY_DESCRIPTOR = sd           # ✅ 보안 설명자 지정
    return sa

def start_pipe_server():
    print(f"📡 메시지 수신 파이프 서버 시작: {PIPE_RECV}")

    sa = get_open_security_attributes()

    pipe = win32pipe.CreateNamedPipe(
        PIPE_RECV,
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
        1, 65536, 65536, 0, sa
    )
    if pipe is None:
        print("❌ 좌표 전송용 파이프가 아직 연결되지 않았습니다.")
        return
    if pipe == win32file.INVALID_HANDLE_VALUE:
        print(f"❌ 파이프 생성 실패: {PIPE_RECV}")
    else:
        print(f"✅ 파이프 생성 성공: {PIPE_RECV}")
    win32pipe.ConnectNamedPipe(pipe, None)

    pipe_connected_event.set()

    print("🔗 Unreal 연결 완료 (수신 전용)")
    handle_client(pipe)

if __name__ == "__main__":
    start_pipe_server()
