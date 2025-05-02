import cv2
import mediapipe as mp
import numpy as np
import pickle
import win32file
from sklearn.linear_model import RidgeCV
from utils.packet_utils import pack_eye_tracking_response_with_header


def run_eye_tracking(screen_w, screen_h, pipe=None, stop_event=None):
    try:
        with open("calibration_map.pkl", "rb") as f:
            calibration_data = pickle.load(f)
    except:
        print("❗ 보정 데이터가 없습니다. 먼저 칼리브레이션을 수행해주세요.")
        return

    # feature: (eye_x, eye_y, pitch, yaw, face_z) / label: (target_x, target_y)
    X = np.array([feat for feat, _ in calibration_data])
    y = np.array([label for _, label in calibration_data])

    # 보정 모델 학습 (RidgeCV)
    model_x = RidgeCV(alphas=[0.1, 1.0, 10.0]).fit(X, y[:, 0])
    model_y = RidgeCV(alphas=[0.1, 1.0, 10.0]).fit(X, y[:, 1])

    cap = cv2.VideoCapture(0)
    face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)

    print("🎯 ML 기반 시선 추적 시작 (Q 누르면 종료)")

    while stop_event is None or not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        canvas = 255 * np.ones((screen_h, screen_w, 3), dtype=np.uint8)

        if result.multi_face_landmarks:
            face = result.multi_face_landmarks[0].landmark
            left_iris = face[468]
            right_iris = face[473]
            eye_x = (left_iris.x + right_iris.x) / 2
            eye_y = (left_iris.y + right_iris.y) / 2
            face_z = (face[1].z + face[10].z + face[152].z) / 3

            dy = face[152].y - face[10].y
            dz1 = face[152].z - face[10].z
            pitch = np.arctan2(dy, dz1)

            dx = face[263].x - face[33].x
            dz2 = face[263].z - face[33].z
            yaw = np.arctan2(dx, dz2)

            # 예측
            features = np.array([[eye_x, eye_y, pitch, yaw, face_z]])
            gaze_x = int(model_x.predict(features)[0])
            gaze_y = int(model_y.predict(features)[0])

            cv2.circle(canvas, (gaze_x, gaze_y), 30, (0, 0, 255), -1)

            if pipe is not None:
                try:
                    packet = pack_eye_tracking_response_with_header(
                        quiz_id=1,
                        x=float(gaze_x),
                        y=float(gaze_y),
                        blink=0,  # 추후 blink 추정 모델 넣을 수 있음
                        state=100
                    )
                    win32file.WriteFile(pipe, packet)
                    print(f"📤 좌표 전송: ({gaze_x}, {gaze_y})")
                except Exception as e:
                    print(f"❌ 파이프 전송 실패: {e}")

        cv2.imshow("Tracking", canvas)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🛑 시선 추적 종료")
