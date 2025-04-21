import time 
import cv2
import mediapipe as mp
import pyautogui
import numpy as np

def run_eye_tracker(q, show_face_mesh=False):
    screen_w, screen_h = pyautogui.size()
    cap = cv2.VideoCapture(0)
    print(f"Camera resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)} x {cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

    if show_face_mesh:
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        cv2.namedWindow("Face Mesh View", cv2.WINDOW_NORMAL)

    cv2.namedWindow("Eye Tracking - Red Dot", cv2.WINDOW_NORMAL)

    calibration_step = 0
    calibration_complete = False
    collected_eye_positions = []
    calibration_eye_distance = None

    min_x, min_y = 1.0, 1.0
    max_x, max_y = 0.0, 0.0

    margin = 50
    corner_points = [
        (margin, margin),
        (screen_w - margin, margin),
        (margin, screen_h - margin),
        (screen_w - margin, screen_h - margin)
    ]
    instructions = [
        "Look at the top-left corner and press 'w'",
        "Look at the top-right corner and press 'w'",
        "Look at the bottom-left corner and press 'w'",
        "Look at the bottom-right corner and press 'w'"
    ]

    def draw_cross(img, center, size=20, color=(0, 0, 0), thickness=2):
        cx, cy = center
        half = size // 2
        cv2.line(img, (cx - half, cy), (cx + half, cy), color, thickness)
        cv2.line(img, (cx, cy - half), (cx, cy + half), color, thickness)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        face_mesh_frame = frame.copy() if show_face_mesh else None
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        screen = 255 * np.ones((screen_h, screen_w, 3), dtype=np.uint8)

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
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1)
                    )

                left_iris = face_landmarks.landmark[468]
                right_iris = face_landmarks.landmark[473]
                eye_x = (left_iris.x + right_iris.x) / 2
                eye_y = (left_iris.y + right_iris.y) / 2

                left_eye_edge = face_landmarks.landmark[33]
                right_eye_edge = face_landmarks.landmark[263]
                current_eye_distance = abs(right_eye_edge.x - left_eye_edge.x)
                eye_center_x = (left_eye_edge.x + right_eye_edge.x) / 2

                if not calibration_complete:
                    if calibration_step < 4:
                        draw_cross(screen, corner_points[calibration_step], 30, (0, 0, 255), 5)
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        text = instructions[calibration_step]
                        (tw, th), _ = cv2.getTextSize(text, font, 0.8, 2)
                        tx = (screen_w - tw) // 2
                        ty = screen_h // 2
                        cv2.putText(screen, text, (tx, ty), font, 0.8, (0, 0, 0), 2)
                    elif calibration_step == 4:
                        xs, ys = zip(*collected_eye_positions)
                        min_x, max_x = min(xs), max(xs)
                        min_y, max_y = min(ys), max(ys)
                        calibration_complete = True
                else:
                    if calibration_eye_distance:
                        scale_ratio = current_eye_distance / calibration_eye_distance
                    else:
                        scale_ratio = 1.0

                    adjusted_x = eye_center_x + (eye_x - eye_center_x) / scale_ratio
                    adjusted_y = eye_y

                    if max_x - min_x == 0 or max_y - min_y == 0:
                        mapped_x, mapped_y = screen_w // 2, screen_h // 2
                    else:
                        mapped_x = int((adjusted_x - min_x) / (max_x - min_x) * screen_w)
                        mapped_y = int((adjusted_y - min_y) / (max_y - min_y) * screen_h)
                    
                    cv2.circle(screen, (mapped_x, mapped_y), 20, (0, 0, 225), -1)
                    q.put((mapped_x, mapped_y))

        key = cv2.waitKey(1) & 0xFF
        if key == ord('w') and not calibration_complete and calibration_step < 4:
            calibration_eye_distance = current_eye_distance
            eye_center_x = (face_landmarks.landmark[33].x + face_landmarks.landmark[263].x) / 2
            adjusted_x = eye_center_x + (eye_x - eye_center_x)
            collected_eye_positions.append((adjusted_x, eye_y))
            calibration_step += 1
        if key == ord('q'):
            break

        cv2.imshow("Eye Tracking - Red Dot", screen)
        if show_face_mesh and face_mesh_frame is not None:
            cv2.imshow("Face Mesh View", face_mesh_frame)

    cap.release()
    cv2.destroyAllWindows()