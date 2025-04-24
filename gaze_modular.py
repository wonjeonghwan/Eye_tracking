import cv2
import mediapipe as mp
import pyautogui
import numpy as np
from utils.face_utils import get_eye_openness, get_face_height
from utils.gaze_utils import compute_relative_gaze, map_calibrated_gaze
from utils.blink_detector import BlinkDetector

def run_gaze_estimation(q, show_face_mesh=False, stop_event=None):
    screen_w, screen_h = pyautogui.size()
    cap = cv2.VideoCapture(0)
    print(f"Gaze Estimation, Camera resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)} x {cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

    if show_face_mesh:
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        cv2.namedWindow("Face Mesh View", cv2.WINDOW_NORMAL)

    cv2.namedWindow("Gaze Estimation", cv2.WINDOW_NORMAL)

    calibration_step = 0
    calibration_complete = False
    calibration_points = []
    calibration_eye_open_list = []

    margin = 50
    corner_points = [
        (margin, margin),
        (screen_w - margin, margin),
        (margin, screen_h - margin),
        (screen_w - margin, screen_h - margin)
    ]
    instructions = [
        "Look at top-left corner and press 'w'",
        "Look at top-right corner and press 'w'",
        "Look at bottom-left corner and press 'w'",
        "Look at bottom-right corner and press 'w'"
    ]

    def draw_cross(img, center, size=20, color=(0, 0, 0), thickness=2):
        cx, cy = center
        half = size // 2
        cv2.line(img, (cx - half, cy), (cx + half, cy), color, thickness)
        cv2.line(img, (cx, cy - half), (cx, cy + half), color, thickness)

    prev_x, prev_y = None, None
    alpha = 0.5
    blink_detector = BlinkDetector(threshold_ratio=0.5, blink_threshold=4)

    while True:
        if stop_event and stop_event.is_set():
            print("stop_event 를 통한 루프 종료")
            break

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        face_mesh_frame = frame.copy() if show_face_mesh else None
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        screen = np.ones((screen_h, screen_w, 3), dtype=np.uint8) * 255

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = face_landmarks.landmark
                eye_openness = get_eye_openness(landmarks)
                face_height = get_face_height(landmarks)
                eye_openness_normalized = eye_openness / face_height if face_height > 0 else 0

                blink_state, blink_count = blink_detector.update(eye_openness_normalized, blink_detector.open_ref)

                if calibration_complete:
                    print(f"Normalized: {eye_openness_normalized:.4f}, Ref: {blink_detector.open_ref:.4f}, Blinked: {blink_state}, Total: {blink_count}")
                else:
                    print(f"Normalized: {eye_openness_normalized:.4f}, Blinked: {blink_state}, Total: {blink_count}")

                if show_face_mesh and face_mesh_frame is not None:
                    mp_drawing.draw_landmarks(
                        image=face_mesh_frame,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
                    )
                    mp_drawing.draw_landmarks(
                        image=face_mesh_frame,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_IRISES,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1)
                    )

                left_iris = face_landmarks.landmark[468]
                right_iris = face_landmarks.landmark[473]
                nose_tip = face_landmarks.landmark[1]

                eye_x = (left_iris.x + right_iris.x) / 2
                eye_y = (left_iris.y + right_iris.y) / 2

                if not calibration_complete:
                    if calibration_step < 4:
                        draw_cross(screen, corner_points[calibration_step], 30, (0, 0, 255), 2)
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        text = instructions[calibration_step]
                        (tw, th), _ = cv2.getTextSize(text, font, 0.8, 2)
                        tx = (screen_w - tw) // 2
                        ty = screen_h // 2
                        cv2.putText(screen, text, (tx, ty), font, 0.8, (0, 0, 0), 2)
                else:
                    gaze_x, gaze_y = map_calibrated_gaze(eye_x, eye_y, calibration_points, screen_w, screen_h, prev_x, prev_y, alpha)
                    prev_x, prev_y = gaze_x, gaze_y
                    cv2.circle(screen, (gaze_x, gaze_y), 20, (0, 0, 255), -1)
                    blink_text = f"Closed Count: {blink_count}"
                    cv2.putText(screen, blink_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                    if not stop_event.is_set():
                        q.put({
                            "type": "response",
                            "data": {
                                "quiz_id": 1,
                                "screen_w": screen_w,
                                "screen_h": screen_h,
                                "x": gaze_x,
                                "y": gaze_y,
                                "blink": int(blink_state),
                                "state": 100
                            }
                        })

        key = cv2.waitKey(1) & 0xFF
        if key == ord('w') and not calibration_complete and calibration_step < 4:
            calibration_points.append((eye_x, eye_y))
            calibration_eye_open_list.append(eye_openness_normalized)
            calibration_step += 1
            if calibration_step == 4:
                blink_detector.open_ref = np.mean(calibration_eye_open_list)
                calibration_complete = True

        if key == ord('q'):
            if stop_event is not None:
                print("🛑 Gaze Estimation 종료 신호 전송")
                stop_event.set()
            break

        cv2.imshow("Gaze Estimation", screen)
        if show_face_mesh and face_mesh_frame is not None:
            cv2.imshow("Face Mesh View", face_mesh_frame)

    cap.release()
    cv2.destroyAllWindows()
