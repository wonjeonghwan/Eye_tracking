from multiprocessing import Process, Queue, Event
from eye_tracker import run_eye_tracker
from gaze_tracker import run_gaze_estimation
from ipc_listener import run_listener
from unreal_pipe_sender import pipe_sender, get_queue, forward_to_unreal
from threading import Thread


def queue_drain_worker(q, stop_event):
    while not stop_event.is_set():
        try:
            q.get(timeout=1)
        except:
            pass

if __name__ == "__main__":
    USE_EYE_TRACKING = True
    USE_GAZE_ESTIMATION = False
    SHOW_FACE_MESH_IN_TRACKER = True
    USE_UNREAL_SEND = False

    stop_event = Event()
    q = Queue()
    processes = []

    if not USE_UNREAL_SEND:
        Thread(target=queue_drain_worker, args=(q, stop_event), daemon=True).start()

    if USE_EYE_TRACKING:
        if USE_GAZE_ESTIMATION:
            processes.append(Process(target=run_gaze_estimation, args=(q, SHOW_FACE_MESH_IN_TRACKER, stop_event)))
        else:
            processes.append(Process(target=run_eye_tracker, args=(q, SHOW_FACE_MESH_IN_TRACKER, stop_event)))
        if USE_UNREAL_SEND:
            processes.append(Process(target=run_listener, args=(q,stop_event)))

    if USE_UNREAL_SEND:
        unreal_q = get_queue()
        # ✅ Thread로 실행 (queue.Queue 호환)
        Thread(target=pipe_sender, daemon=True).start()
        Thread(target=forward_to_unreal, args=(q, unreal_q), daemon=True).start()

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    try:
        q.close()
        q.join_thread()
        print("✅ main.py: Queue 닫기 완료")
    except Exception as e:
        print(f"⚠️ main.py: Queue 종료 중 오류: {e}")

    print("✅ 모든 프로세스 정상 종료")