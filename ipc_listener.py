import time

def run_listener(q, stop_event=None):
    print("👂 IPC Listener started!")
    while True:
        if stop_event and stop_event.is_set():
            print("IPC Listener 종료됨")
            break
        if not q.empty():
            x, y = q.get()
            print(f"📍 Received via IPC: ({x}, {y})")
        
        else:
            time.sleep(1)
        