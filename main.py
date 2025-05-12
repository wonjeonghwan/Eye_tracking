import threading
from pipe_server import start_pipe_server, pipe_connected_event
from utils.packet_utils import start_coordinate_pipe_server

if __name__ == "__main__":
    print("🔌 Unreal용 Named Pipe 서버 실행 중...")

    # 메시지 수신 서버 (start/end)
    t1 = threading.Thread(target=start_pipe_server)
    t1.start()

    # pipe_connected_event.wait()

    # 좌표 전송 파이프 서버
    t2 = threading.Thread(target=start_coordinate_pipe_server)
    t2.start()
