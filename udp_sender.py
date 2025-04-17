import socket
import os
from dotenv import load_dotenv

load_dotenv()

class UDPSender:
    def __init__(self):
        ip = os.getenv("UDP_IP", "127.0.0.1")
        port = int(os.getenv("UDP_PORT", "6000"))
        self.addr = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_coords(self, x, y):
        message = f"{x},{y}\n".encode('utf-8')
        self.sock.sendto(message, self.addr)

# 이하 로그 테스트
print("Loaded IP:", os.getenv("UDP_IP"))
print("Loaded PORT:", os.getenv("UDP_PORT"))