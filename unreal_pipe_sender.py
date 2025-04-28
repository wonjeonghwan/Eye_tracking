import win32pipe, win32file, pywintypes
import struct
import threading
from utils.packet_utils import pack_eye_tracking_response

PIPE_NAME = r'\\.\pipe\unreal_pipe'
NOTIFY_STRUCT_FORMAT = '<BBBB'  # QuizID, SettingStart, Start, End

def start_pipe_server(stop_event=None, pipe_ready_event=None):
    print(f"📡 [Pipe] Named Pipe 서버 모드 시작 대기 중: {PIPE_NAME}")
    pipe = win32pipe.CreateNamedPipe(
        PIPE_NAME,
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
        2, 65536, 65536, 0, None
    )
    print("🕒 [Pipe] Named Pipe 생성 완료, ConnectNamedPipe() 호출 준비 (메인 스레드)")
    try:
        win32pipe.ConnectNamedPipe(pipe, None)
        print("🔗 [Pipe] ConnectNamedPipe 연결 완료")

        if pipe_ready_event:
            pipe_ready_event.set()

        print("🎯 [Pipe] 클라이언트 연결 대기 중")
        handle_client(pipe, stop_event)

    except Exception as e:
        print(f"❌ [Pipe] 연결 실패: {e}")
    finally:
        print("⚡ [Pipe] Named Pipe 핸들 닫기")
        win32file.CloseHandle(pipe)


    thread = threading.Thread(target=wait_and_start)
    thread.daemon = True
    thread.start()

def handle_client(pipe, stop_event):
    print("👂 [Pipe] 클라이언트 통신 루프 진입")
    while True:
        try:
            data = win32file.ReadFile(pipe, 4)[1]
            print(f"📨 [Pipe] 데이터 수신 (길이 {len(data)} bytes)")

            if len(data) == 4:
                quiz_id, setting_start, start, end = struct.unpack(NOTIFY_STRUCT_FORMAT, data)
                print(f"📥 [Pipe] Notify 수신 → QuizID={quiz_id}, SettingStart={setting_start}, Start={start}, End={end}")

                if setting_start == 1:
                    print("🛠️ [Pipe] 캘리브레이션 시작 신호 수신됨")
                elif start == 1:
                    print("▶️ [Pipe] 게임 시작 신호 수신됨")
                elif end == 1:
                    print("⛔ [Pipe] 게임 종료 신호 수신됨")
                    if stop_event:
                        stop_event.set()

                response = pack_eye_tracking_response(quiz_id, 500.0, 300.0, 0, 1)
                win32file.WriteFile(pipe, response)
                print("🚀 [Pipe] 응답 전송 완료")

        except pywintypes.error as e:
            if e.winerror == 109:
                print("❌ [Pipe] 클라이언트 연결 종료됨 (Unreal 연결 끊김)")
            else:
                print(f"❌ [Pipe] 통신 오류: {e}")
            break
