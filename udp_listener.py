import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", 6000))
print("Listening on 127.0.0.1:6000")

while True:
    data, addr = sock.recvfrom(1024)
    print("Received:", data.decode().strip())