# 눈을 뜬 정도
def get_eye_openness(landmarks, top_idx=159, bottom_idx=145):
    top = landmarks[top_idx].y          # top은 왼쪽 위 눈커풀 y좌표
    bottom = landmarks[bottom_idx].y    # bottom은 왼쪽 아래 눈커풀 y좌표
    return abs(bottom - top)

# 얼굴 세로 높이
def get_face_height(landmarks, top_idx=10, bottom_idx=152):
    top = landmarks[top_idx].y
    bottom = landmarks[bottom_idx].y
    return abs(bottom - top)

# 눈 뜬 정도 정규화
def get_normalized_eye_openness(landmarks):
    eye_open = get_eye_openness(landmarks)
    face_height = get_face_height(landmarks)
    return eye_open / face_height if face_height > 0 else 0
    # 눈 뜬 정도