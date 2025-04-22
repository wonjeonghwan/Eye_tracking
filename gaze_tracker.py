import cv2
import mediapipe as mp
import pyautogui
import numpy as np

def run_gaze_estimation(q, show_face_mesh=False, stop_event=None):
    screen_w, screen_h = pyautogui.size()
    cap = cv2.VideoCapture(0)
    print("🎯 Gaze Estimation 시작")

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
    margin = 50
    corner_points = [
        (margin, margin),  # top-left
        (screen_w - margin, margin),  # top-right
        (margin, screen_h - margin),  # bottom-left
        (screen_w - margin, screen_h - margin)  # bottom-right
    ]
    instructions = [
        "Look at top-left corner and press 'w'",
        "Look at top-right corner and press 'w'",
        "Look at bottom-left corner and press 'w'",
        "Look at bottom-right corner and press 'w'"
    ]

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
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0,255,0), thickness=1)
                    )
                left_iris = face_landmarks.landmark[468]
                right_iris = face_landmarks.landmark[473]
                nose_tip = face_landmarks.landmark[1]

                eye_x = (left_iris.x + right_iris.x) / 2
                eye_y = (left_iris.y + right_iris.y) / 2

                dx = eye_x - nose_tip.x
                dy = eye_y - nose_tip.y

                gaze_x = int((0.5 + dx * 5) * screen_w)
                gaze_y = int((0.5 + dy * 5) * screen_h)

                gaze_x = np.clip(gaze_x, 0, screen_w - 1)
                gaze_y = np.clip(gaze_y, 0, screen_h - 1)

                cv2.circle(screen, (gaze_x, gaze_y), 20, (255, 0, 0), -1)
                if not stop_event.is_set():
                    q.put((gaze_x, gaze_y))# ✅ IPC로 전송

                if not calibration_complete:
                    if calibration_step < 4:
                        # 보정용 십자 표시
                        cv2.circle(screen, corner_points[calibration_step], 30, (0, 0, 255), -1)
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        text = instructions[calibration_step]
                        (tw, th), _ = cv2.getTextSize(text, font, 0.8, 2)
                        tx = (screen_w - tw) // 2
                        ty = screen_h // 2
                        cv2.putText(screen, text, (tx, ty), font, 0.8, (0, 0, 0), 2)
                else:
                    # 눈 위치를 보정된 화면 좌표로 매핑
                    xs, ys = zip(*calibration_points)
                    min_x, max_x = min(xs), max(xs)
                    min_y, max_y = min(ys), max(ys)

                    range_x = max_x - min_x
                    range_y = max_y - min_y

                    dx = eye_x
                    dy = eye_y

                    if range_x == 0 or range_y == 0:
                        mapped_x, mapped_y = screen_w // 2, screen_h // 2
                    else:
                        mapped_x = int((dx - min_x) / range_x * screen_w)
                        mapped_y = int((dy - min_y) / range_y * screen_h)

                    mapped_x = np.clip(mapped_x, 0, screen_w - 1)
                    mapped_y = np.clip(mapped_y, 0, screen_h - 1)

                    cv2.circle(screen, (mapped_x, mapped_y), 20, (0, 0, 255), -1)
                    if not stop_event.is_set():
                        q.put((mapped_x, mapped_y))



        key = cv2.waitKey(1) & 0xFF
        if key == ord('w') and not calibration_complete and calibration_step < 4:
            calibration_points.append((eye_x, eye_y))
            calibration_step += 1
            if calibration_step == 4:
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