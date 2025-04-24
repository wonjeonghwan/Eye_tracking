import time

def run_listener(q, stop_event=None):
    print("👂 IPC Listener started!")
    while True:
        if stop_event and stop_event.is_set():
            print("IPC Listener 종료됨")
            break
        try:
            x, y = q.get(timeout=1)
            print(f"📍 Received via IPC: ({x}, {y})")
        except:
            continue
        