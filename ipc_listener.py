import time

def run_listener(q):
    print("👂 IPC Listener started!")
    while True:
        if not q.empty():
            x, y = q.get()
            print(f"📍 Received via IPC: ({x}, {y})")
        else:
            time.sleep(1)