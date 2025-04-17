import socket

class UDPSender:
    def __init__(self, ip='127.0.0.1', port=5050):
        self.addr = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_coords(self, x, y):
        message = f"{x},{y}\n".encode('utf-8')
        self.sock.sendto(message, self.addr)
