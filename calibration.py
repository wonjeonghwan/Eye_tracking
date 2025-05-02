import cv2
import time
import mediapipe as mp
import numpy as np
import pickle
import math

# 공통 설정
RADIUS = 30
FPS = 30
DURATION_PER_STEP = 3  # 초 단위
GRID_POINTS = [(x, y) for y in [0.25, 0.5, 0.75] for x in [0.25, 0.5, 0.75]]

mp_face = mp.solutions.face_mesh

def wait_for_w(screen_w, screen_h, message):
    cv2.namedWindow("Calibration", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Calibration", 1280, 800)
    while True:
        canvas = 255 * np.ones((screen_h, screen_w, 3), dtype=np.uint8)
        cv2.putText(canvas, message, (100, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3)
        cv2.imshow("Calibration", canvas)
        key = cv2.waitKey(1)
        if key & 0xFF == ord('w'):
            return
        elif key & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            exit()

def extract_feature(landmarks):
    left_iris = landmarks[468]
    right_iris = landmarks[473]
    eye_x = (left_iris.x + right_iris.x) / 2
    eye_y = (left_iris.y + right_iris.y) / 2
    face_z = (landmarks[1].z + landmarks[10].z + landmarks[152].z) / 3
    pitch = math.atan2(landmarks[152].y - landmarks[10].y, landmarks[152].z - landmarks[10].z)
    yaw = math.atan2(landmarks[263].x - landmarks[33].x, landmarks[263].z - landmarks[33].z)
    return (eye_x, eye_y, pitch, yaw, face_z)

def run_z_path_calibration(cap, face_mesh, screen_w, screen_h, margin):
    print("▶️ Z자 경로 캘리브레이션 시작")
    safe_margin = margin + RADIUS
    checkpoints = [
        (safe_margin, safe_margin),
        (screen_w - safe_margin, safe_margin),
        (safe_margin, screen_h - safe_margin),
        (screen_w - safe_margin, screen_h - safe_margin)
    ]
    total_segments = len(checkpoints) - 1
    total_duration = DURATION_PER_STEP * total_segments
    start_time = time.time()
    data = []

    while True:
        now = time.time()
        elapsed = now - start_time
        if elapsed > total_duration:
            break

        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        segment_idx = int(elapsed // DURATION_PER_STEP)
        t = (elapsed % DURATION_PER_STEP) / DURATION_PER_STEP
        (x0, y0), (x1, y1) = checkpoints[segment_idx], checkpoints[segment_idx + 1]
        target_x = int((1 - t) * x0 + t * x1)
        target_y = int((1 - t) * y0 + t * y1)

        canvas = 255 * np.ones((screen_h, screen_w, 3), dtype=np.uint8)
        cv2.circle(canvas, (target_x, target_y), RADIUS, (0, 255, 0), -1)
        cv2.imshow("Calibration", canvas)

        result = face_mesh.process(rgb)
        if result.multi_face_landmarks:
            feature = extract_feature(result.multi_face_landmarks[0].landmark)
            data.append((feature, (target_x, target_y)))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    return data

def run_nine_point_calibration(cap, face_mesh, screen_w, screen_h):
    print("▶️ 9점 고정 캘리브레이션 시작")
    data = []
    for gx, gy in GRID_POINTS:
        target_x = int(screen_w * gx)
        target_y = int(screen_h * gy)
        start_time = time.time()

        while time.time() - start_time < 1.0:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            canvas = 255 * np.ones((screen_h, screen_w, 3), dtype=np.uint8)
            cv2.circle(canvas, (target_x, target_y), RADIUS, (0, 255, 0), -1)
            cv2.imshow("Calibration", canvas)

            result = face_mesh.process(rgb)
            if result.multi_face_landmarks:
                feature = extract_feature(result.multi_face_landmarks[0].landmark)
                data.append((feature, (target_x, target_y)))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    return data

def run_circle_path_calibration(cap, face_mesh, screen_w, screen_h):
    print("▶️ 원형 경로 캘리브레이션 시작")
    data = []
    cx, cy = screen_w // 2, screen_h // 2
    r = min(screen_w, screen_h) // 3
    duration = 10  # 초
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed > duration:
            break
        angle = 2 * math.pi * (elapsed / duration)
        target_x = int(cx + r * math.cos(angle))
        target_y = int(cy + r * math.sin(angle))

        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        canvas = 255 * np.ones((screen_h, screen_w, 3), dtype=np.uint8)
        cv2.circle(canvas, (target_x, target_y), RADIUS, (0, 255, 0), -1)
        cv2.imshow("Calibration", canvas)

        result = face_mesh.process(rgb)
        if result.multi_face_landmarks:
            feature = extract_feature(result.multi_face_landmarks[0].landmark)
            data.append((feature, (target_x, target_y)))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    return data

def run_full_calibration(screen_w, screen_h, margin=40):
    cap = cv2.VideoCapture(0)
    face_mesh = mp_face.FaceMesh(refine_landmarks=True)
    total_data = []

    wait_for_w(screen_w, screen_h, "Start Ztype calibrations with press 'W'")
    total_data += run_z_path_calibration(cap, face_mesh, screen_w, screen_h, margin)

    wait_for_w(screen_w, screen_h, "Start 9-points calibrations with press 'W'")
    total_data += run_nine_point_calibration(cap, face_mesh, screen_w, screen_h)

    wait_for_w(screen_w, screen_h, "Start circular calibrations with press 'W'")
    total_data += run_circle_path_calibration(cap, face_mesh, screen_w, screen_h)

    cap.release()
    cv2.destroyAllWindows()

    with open("calibration_map.pkl", "wb") as f:
        pickle.dump(total_data, f)

    print(f"✅ 전체 캘리브레이션 완료: 총 {len(total_data)} 샘플 수집됨")