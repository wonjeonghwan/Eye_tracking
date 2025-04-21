# unreal_pipe_sender.py
import os
import time
import threading
import queue

PIPE_NAME = r'\\.\pipe\unreal_pipe'
_q = queue.Queue()

def pipe_sender():
    print(f"📡 Unreal 파이프로 전송 시도 중: {PIPE_NAME}")
    while True:
        try:
            with open(PIPE_NAME, 'w') as pipe:
                print("✅ Unreal과 파이프 연결됨")
                while True:
                    coords = _q.get()
                    if isinstance(coords, tuple):
                        x, y = coords
                        message = f"{x},{y}\n"
                        pipe.write(message)
                        pipe.flush()
                        print(f"🚀 보냄 → {message.strip()}")
        except Exception as e:
            print(f"❌ 파이프 연결 실패, 재시도 중... ({e})")
            time.sleep(1)

def get_queue():
    return _q

# 🔁 다른 큐에서 받아서 이 모듈의 q로 옮기는 함수
def forward_to_unreal(src_q, dest_q):
    while True:
        if not src_q.empty():
            dest_q.put(src_q.get())
        else:
            time.sleep(0.005)
