from pipe_server import start_pipe_server
import threading

if __name__ == "__main__":
    print("🔌 Unreal용 Named Pipe 서버 실행 중...")
    stop_event = threading.Event()
    start_pipe_server(stop_event=stop_event)
