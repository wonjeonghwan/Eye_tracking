import time             # 타이밍 제어, sleep 등 활용
import cv2              # OpenCV. 영상 입력, 시각화 등
import mediapipe as mp  # 얼굴/손 추적 라이브러리, 얼굴 랜드마크 인식
import pyautogui        # 현재 화면 해상도 가져오기 위함
import numpy as np      

def run_eye_tracker(q, show_face_mesh=False, stop_event=None):
    screen_w, screen_h = pyautogui.size()       # 현재 모니터의 해상도를 가져옴
    cap = cv2.VideoCapture(0)                   # 노트북 카메라 캡쳐
    print(f"Camera resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)} x {cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}") # 카메라 해상도 값 출력
    mp_face_mesh = mp.solutions.face_mesh                       # 얼굴 인식 클래스 가져옴
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)    # refine_landmarks 를통해 개선된 모델(홍채, 눈, 입술 랜드마크에 포함) 사용

    if show_face_mesh:      # 얼굴 메쉬를 불러온다면
        mp_drawing = mp.solutions.drawing_utils                 # 얼굴에 선, 점 등을 그리는 기능을 불러온 걸 담은 객체
        mp_drawing_styles = mp.solutions.drawing_styles         # 파란 선, 초록 점 등 Google의 기본 스타일 세트를 담은 객체
        cv2.namedWindow("Face Mesh View", cv2.WINDOW_NORMAL)    

    cv2.namedWindow("Eye Tracking - Red Dot", cv2.WINDOW_NORMAL)

    calibration_step = 0            # 현재 보정 중인 코너
    calibration_complete = False    # 보정 완료 여부
    collected_eye_positions = []    # 수집된 눈 위치 데이터
    calibration_eye_distance = None # 눈 거리 기준 조정에 빈 값을 둠 (이후에 쓰겠다는 뜻)

    min_x, min_y = 1.0, 1.0     #가장 작은 x,y값을 설정(가장 크게)
    max_x, max_y = 0.0, 0.0     #가장 큰 x,y값을 설정(가장 작게)

    margin = 50         # 모서리 좌표값
    corner_points = [   # 4개의 각 모서리 위치 지정
        (margin, margin),
        (screen_w - margin, margin),
        (margin, screen_h - margin),
        (screen_w - margin, screen_h - margin)
    ]
    instructions = [    # 각 모서리 안내
        "Look at the top-left corner and press 'w'",
        "Look at the top-right corner and press 'w'",
        "Look at the bottom-left corner and press 'w'",
        "Look at the bottom-right corner and press 'w'"
    ]

    def draw_cross(img, center, size=20, color=(0, 0, 0), thickness=2): # 화면에 표시할 십자가를 그리는 코드
        cx, cy = center
        half = size // 2
        cv2.line(img, (cx - half, cy), (cx + half, cy), color, thickness)
        cv2.line(img, (cx, cy - half), (cx, cy + half), color, thickness)

    # 보간용 초기화
    prev_x, prev_y = None, None
    alpha = 0.3 # 부드러움 정도 (0.1 ~ 0.3 추천)

    while True:
        ret, frame = cap.read() # 위의 cv2.VideoCapture(0)를 읽어오는 함수, ret(return)은 프레임을 정상적으로 읽었는지 여부. frame은 영상데이터
        if not ret:
            break

        frame = cv2.flip(frame, 1)  # 이미지 반전, frame = 원본이미지, 1=좌우 반전, 0=상하반전, -1=상하+좌우 반전
        
        face_mesh_frame = frame.copy() if show_face_mesh else None  # face.copy = 프레임을 복제하여 저장, 나중에 이 복사본 위에 따로 표시 예정
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # cvtColor = Convert Color, BGR로 색상을 표현하는 순서만 RGB로 변환
        results = face_mesh.process(rgb_frame)  # result에, 위에서 정의한 미디어파이프 모델을 rgb_frame을 반영해서 넣어서 실행시킴

        screen = 255 * np.ones((screen_h, screen_w, 3), dtype=np.uint8) # np.ones(1로 채움)(screen_h = 가로, screen_w = 세로, 3 = 채널) 이후 255로 곱합
        # dtype = data type, Numpy 배열에 들어가는 값이 어떤 형태(int, float, bool)인지
        # uint8 = Unsigned Integer 8bit(부호없는 8비트 정수), 2의 8제곱을 0부터 하면 총 256개.
        if results.multi_face_landmarks:    # result에서 얼굴 주요 지점 정보가 들어온다면
            for face_landmarks in results.multi_face_landmarks: # 각 주요 지점별로
                if show_face_mesh and face_mesh_frame is not None:  # 얼굴 메쉬가 잘 들어왔고, 얼굴 프레임도 잘 들어왔다면
                    mp_drawing.draw_landmarks(                      # 그림 기능에서 주요 지점 그리는 것에서 다음을 가져온다(호출, 실행)
                        image=face_mesh_frame,                      # 그림 그릴 대상 = 얼굴 프레임
                        landmark_list=face_landmarks,               # 주요 지점 리스트 = 얼굴 주요 지점
                        connections=mp_face_mesh.FACEMESH_TESSELATION,  # 연결 = 얼굴 메쉬에서 테셀레이션(겹치지 않게 공간을 채우는 것)
                        landmark_drawing_spec=None,                 # 점을 어떻게 표시할 것 인지 = 기본
                        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
                        # 선을 어떻게 표시할 것 인지 = 기본 face_mesh_tesselation 스타일
                    )
                    # mp_drawing.draw_landmarks(                      # 그림 기능에서 주요 지점에 접근하여 아래를 가져온다(호출, 실행)
                    #     image=face_mesh_frame,                      # 그림 그릴 대상 = 얼굴 프레임
                    #     landmark_list=face_landmarks,               # 주요 지점 리스트 = 얼굴의 주요 지점
                    #     connections=mp_face_mesh.FACEMESH_IRISES,   # 연결 = 얼굴 메쉬에서 홍채
                    #     landmark_drawing_spec=None,                 # 점 표시 = 기본
                    #     connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1)
                    #     # 선을 어떻게 표시할건가 = 미디어파이프 그리기에서, 그리는 사양.(B, G, R)
                    # )

                left_iris = face_landmarks.landmark[468]    # 왼쪽 눈동자 = 모든 얼굴 주요지표에서. 468번째(홍채 중심)
                right_iris = face_landmarks.landmark[473]   # 오른쪽 눈동자 = 473번째(홍채 중심)
                eye_x = (left_iris.x + right_iris.x) / 2    # 눈동자의 시선 중 x좌표의 중간값
                eye_y = (left_iris.y + right_iris.y) / 2    # 눈동자의 시선 중 y좌표의 중간값

                left_eye_edge = face_landmarks.landmark[33]                     # 왼쪽 눈 꼬리
                right_eye_edge = face_landmarks.landmark[263]                   # 오른쪽 눈 꼬리 (눈 가로 너비 측정용)
                current_eye_distance = abs(right_eye_edge.x - left_eye_edge.x)  # 현재 얼굴 가로의 크기
                eye_center_x = (left_eye_edge.x + right_eye_edge.x) / 2         # 눈 양 끝점의 중간점

                if not calibration_complete:    # 칼리브레이션이 안되었다면 (보정 시작 한다는 뜻)
                    if calibration_step < 4:    # 보정 중인지 확인(총 4번 하니까)
                        draw_cross(screen, corner_points[calibration_step], 30, (0, 0, 255), 5) 
                        # 십자가를 그린다, corner = 위에 지전한 모서리 위치, 크기, 선(BGR)
                        font = cv2.FONT_HERSHEY_SIMPLEX         # 폰트
                        text = instructions[calibration_step]   # 사전에 지정한 안내 문구
                        (tw, th), _ = cv2.getTextSize(text, font, 0.8, 2)   # 텍스트의 가로, 세로 크기 지정, _ =최저 높이(글자가 바닥에 닿는)를 안씀
                        tx = (screen_w - tw) // 2       # 텍스트를 가로 중앙에 위치하기 위한 계산(텍스트 길이 빼고 /2)
                        ty = screen_h // 2              # 텍스트를 세로 중앙에 위치하기 위한 계산
                        cv2.putText(screen, text, (tx, ty), font, 0.8, (0, 0, 0), 2)
                    elif calibration_step == 4:                 # 칼리브레이션 완료 되었다면
                        xs, ys = zip(*collected_eye_positions)  # zip(*) = unpacking, 튜플로
                        min_x, max_x = min(xs), max(xs)         # 최소, 최대 x값(최대 범위)
                        min_y, max_y = min(ys), max(ys)         # 최소, 최대 y값(최대 범위)
                        calibration_complete = True             # 칼리브레이션 완료
                else:                           # 칼리브레이션 완료 후
                    if calibration_eye_distance:# 눈 사이 칼리브레이션을 한다면
                        scale_ratio = current_eye_distance / calibration_eye_distance   # 크기값 설정 = 눈 가로 크기 / 칼리브레이션 값
                    else:
                        scale_ratio = 1.0       # 안하면 그냥 1

                    adjusted_x = eye_center_x + (eye_x - eye_center_x) / scale_ratio
                    # 조정한 x값 = 눈 양끝 중간점 + (동공x중간 - 눈 양끝 중간) / 비율
                    adjusted_y = eye_y  # 동공 y 중간

                    # 이하 화면의 상대 위치 적용 개념
                    if max_x - min_x == 0 or max_y - min_y == 0:            # 만약 보정 좌표의 최소와 최대가 같다면
                        mapped_x, mapped_y = screen_w // 2, screen_h // 2   # 화면 정중앙으로 설정
                    else:
                        mapped_x = int((adjusted_x - min_x) / (max_x - min_x) * screen_w)
                        # 표시할 x값 = ((조정한 x값 - 최소x값) / (최대x값 - 최소x값) * 화면 너비)
                        mapped_y = int((adjusted_y - min_y) / (max_y - min_y) * screen_h)
                        # 표시할 y값 = ((조정한 y값 - 최소y값) / (최대y값 - 최소y값) * 화면 높이)                    
                    # 보간 적용
                    if prev_x is not None and prev_y is not None:   #처음 시작할 때 이전 좌표가 없기 때문에, 있을 때에만 실행
                        mapped_x = int(alpha * mapped_x + (1 - alpha) * prev_x) #좌표 = 조정값 * 위치 + (1-조정값) * 이전 값
                        mapped_y = int(alpha * mapped_y + (1 - alpha) * prev_y) 

                    prev_x, prev_y = mapped_x, mapped_y     # 이전 값 = 현재 값

                    cv2.circle(screen, (mapped_x, mapped_y), 20, (0, 255, 0), -1)   # 원을 그린다(화면에, 보정된 위치에, 크기, 색상, 채우기(-1=꽉참)
                    q.put((mapped_x, mapped_y))     # Queue에다가 해당 좌표값 넣기

        key = cv2.waitKey(1) & 0xFF #key 는 입력을 1밀리초 동안 기다리고 + 8비트 8비트(ASCII) 마스킹이다
        if key == ord('w') and not calibration_complete and calibration_step < 4:
            # w를 눌렀을 때, 그리고 칼리브레이션이 완료되지 않았을 때
            calibration_eye_distance = current_eye_distance # 조정한 눈간 거리 = 지금 눈간 거리
            eye_center_x = (face_landmarks.landmark[33].x + face_landmarks.landmark[263].x) / 2
            # 눈 중간값 = (얼굴 주요 지표.왼쪽눈 바깥 끝.의x값 + 얼굴 주요 지표.오른눈 바깥 끝.의x값) /2
            adjusted_x = eye_center_x + (eye_x - eye_center_x)
            # 조정된 x = 눈 중간값 + (x값 - 눈 중간값)
            collected_eye_positions.append((adjusted_x, eye_y)) # 눈 위치에 보정된 x값,y 저장
            calibration_step += 1                               # 칼리브레이션 진행에 +1
        if key == ord('q'):                                     # q누르면(113)
            if stop_event is not None:                          # stop_event가 들어오면(기존 설정한 None에서 바뀌면)
                print("stop sign sent from 'eye_tracker.py'")   # 출력 하고
                stop_event.set()                                # stop_evet에서 set으로 이동한다
            break                                               # 중지한다

        cv2.imshow("Eye Tracking - Red Dot", screen)            # 위에 circle로 그려놓은걸"Eye Track..."에 보여준다
        if show_face_mesh and face_mesh_frame is not None:
            cv2.imshow("Face Mesh View", face_mesh_frame)

    cap.release()               # 카메라 캡쳐 끊어라
    cv2.destroyAllWindows()     # OpenCV창 모두 닫아라