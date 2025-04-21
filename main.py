from multiprocessing import Process, Queue
from eye_tracker import run_eye_tracker
# from face_mesh_viewer import run_face_mesh_viewer
from ipc_listener import run_listener
from unreal_pipe_sender import pipe_sender, get_queue, forward_to_unreal
from threading import Thread

if __name__ == "__main__":
    USE_EYE_TRACKING = True
    SHOW_FACE_MESH_IN_TRACKER = True
    USE_UNREAL_SEND = False

    q = Queue()
    processes = []

    if USE_EYE_TRACKING:
        processes.append(Process(target=run_eye_tracker, args=(q, SHOW_FACE_MESH_IN_TRACKER)))
        processes.append(Process(target=run_listener, args=(q,)))

    if USE_UNREAL_SEND:
        unreal_q = get_queue()
        # ✅ Thread로 실행 (queue.Queue 호환)
        Thread(target=pipe_sender, daemon=True).start()
        Thread(target=forward_to_unreal, args=(q, unreal_q), daemon=True).start()

    for p in processes:
        p.start()

    for p in processes:
        p.join()
