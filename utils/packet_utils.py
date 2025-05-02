import struct

def pack_eye_tracking_response_with_header(quiz_id, x, y, blink, state):
    """
    Unreal로 전송할 패킷을 Header + Payload 구조로 생성

    - Header: message_type (1B), payload_size (2B), session_id (100B), player_id (1B)
    - Payload: quiz_id (1B), x (float), y (float), blink (1B), state (1B)
    """
    # Payload 구성
    payload = struct.pack('<BffBB', quiz_id, x, y, blink, state)

    # Header 구성
    message_type = 8  # EyeTrackingResponseMessage
    session_id = bytes([1, 0, 0, 0]) + bytes(96)  # 100B 총합
    player_id = 1
    payload_size = len(payload) + 1 + 2 + 100 + 1  # 전체 길이
    header = struct.pack('<BH100sB', message_type, payload_size, session_id, player_id)

    return header + payload