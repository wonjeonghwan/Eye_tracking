from multiprocessing import Process, Event
from gaze_modular import run_gaze_estimation
from unreal_pipe_sender import start_pipe_server

if __name__ == "__main__":
    USE_GAZE_ESTIMATION = True
    USE_PIPE_SERVER = True
    SHOW_FACE_MESH_IN_TRACKER = True

    stop_event = Event()
    pipe_ready_event = Event()
    processes = []

    if USE_PIPE_SERVER:
        processes.append(Process(target=start_pipe_server, args=(stop_event, pipe_ready_event)))

    for p in processes:
        p.start()

    print("🕓 파이프 서버 준비 대기 중...")
    pipe_ready_event.wait()  # 서버 준비 완료까지 대기
    print("✅ 파이프 서버 준비 완료")

    if USE_GAZE_ESTIMATION:
        processes.append(Process(target=run_gaze_estimation, args=(None, SHOW_FACE_MESH_IN_TRACKER, stop_event, pipe_ready_event)))

    for p in processes[1:]:
        p.start()

    for p in processes:
        p.join()
