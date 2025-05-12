# packet_utils.py
import struct
import threading
import win32pipe
import win32file

pipe_ready_event = threading.Event()

PIPE_SEND = r"\\.\pipe\python_to_unreal"
_server_pipe = None  # 내부에서 생성한 pipe를 저장


def pack_eye_tracking_response_with_header(quiz_id, x, y, blink, state):
    """
    Unreal로 전송할 패킷을 Header + Payload 구조로 생성
    """
    payload = struct.pack('<BffBB', quiz_id, x, y, blink, state)

    message_type = 8  # EyeTrackingResponseMessage
    session_id = bytes([1, 0, 0, 0]) + bytes(96)  # 100B
    player_id = 1
    payload_size = len(payload) + 1 + 2 + 100 + 1
    header = struct.pack('<BH100sB', message_type, payload_size, session_id, player_id)

    return header + payload


def start_coordinate_pipe_server():
    global _server_pipe

    print(f"📡 좌표 전송 파이프 서버 시작: {PIPE_SEND}")
    _server_pipe = win32pipe.CreateNamedPipe(
        PIPE_SEND,
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
        1, 65536, 65536, 0, None
    )
    if _server_pipe == win32file.INVALID_HANDLE_VALUE:
        print(f"❌ 파이프 생성 실패: {PIPE_SEND}")
    else:
        print(f"✅ 파이프 생성 성공: {PIPE_SEND}")
    win32pipe.ConnectNamedPipe(_server_pipe, None)
    print("🔗 Unreal과 좌표 전송용 파이프 연결 완료")
    pipe_ready_event.set()


def get_coordinate_pipe():
    pipe_ready_event.wait()  # 🚨 연결 완료까지 대기
    return _server_pipe
