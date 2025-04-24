import cv2
import mediapipe as mp
import pyautogui
import numpy as np

def run_gaze_estimation(q, show_face_mesh=False, stop_event=None):
    screen_w, screen_h = pyautogui.size()   # 현재 모니터 해상도
    cap = cv2.VideoCapture(0)               # 노트북 카메라 캡쳐
    print(f"Gaze Estimation, Camera resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)} x {cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")

    mp_face_mesh = mp.solutions.face_mesh                       # 얼굴 인식 클래스
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)    # 얼굴 메쉬 중 refine_landmarks 반영(홍채)

    if show_face_mesh:        # 얼굴 메쉬 불러올 때
        mp_drawing = mp.solutions.drawing_utils                 # 얼굴에 그리는 기능
        mp_drawing_styles = mp.solutions.drawing_styles         # 그리는 스타일 셋 가져옴
        cv2.namedWindow("Face Mesh View", cv2.WINDOW_NORMAL)    # "Face Mesh View" 창 열기

    cv2.namedWindow("Gaze Estimation", cv2.WINDOW_NORMAL)       # "Gaze Estimation" 창 열기

    calibration_step = 0            # 현재 보정 중인 코너
    calibration_complete = False    # 보정 완료 여부
    calibration_points = []         # 수집된 눈 위치 저장

    open_ref = None # 눈 떠있는 기준 적용
    was_closed = False
    calibration_eye_open_list = []

    margin = 50         # 모서리 좌표 기준
    corner_points = [
        (margin, margin),  # top-left
        (screen_w - margin, margin),  # top-right
        (margin, screen_h - margin),  # bottom-left
        (screen_w - margin, screen_h - margin)  # bottom-right
    ]
    instructions = [    # 각 모서리 안내
        "Look at top-left corner and press 'w'",
        "Look at top-right corner and press 'w'",
        "Look at bottom-left corner and press 'w'",
        "Look at bottom-right corner and press 'w'"
    ]

    def draw_cross(img, center, size=20, color=(0, 0, 0), thickness=2): # 화면에 표시할 십자가를 그리는 코드
        cx, cy = center
        half = size // 2
        cv2.line(img, (cx - half, cy), (cx + half, cy), color, thickness)
        cv2.line(img, (cx, cy - half), (cx, cy + half), color, thickness)

    # 보간용 초기화
    prev_x, prev_y = None, None
    alpha = 0.5 # 부드러움 정도 (0.1 ~ 0.3 추천)

    # Blink 정보
    blink_frame_count = 0   # 눈을 연속으로 감은 프레임 수
    blink_threshold = 4     # 눈 감은 상태 기준
    blinked_count = 0       # 총 눈 감은 횟수
    bBlink = 0              # Unreal 전송용 상태값

    while True:
        if stop_event and stop_event.is_set():  # Stop event가 실행되면
            print("stop_event 를 통한 루프 종료")
            break                               # 종료

        ret, frame = cap.read()                 # ret = 프레임 정상적으로 읽었는지 여부, frame = 영상데이터
        if not ret:                             # 정상적으로 못 읽으면
            break                               # 종료

        frame = cv2.flip(frame, 1)              # frame 의 이미지를 좌우 반전
        face_mesh_frame = frame.copy() if show_face_mesh else None  # 메쉬를 본다면, frame을 복사하여 저장
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # BGR을 RGB로 변환하여 저장
        results = face_mesh.process(rgb_frame)              # rgb_frame를 사전에 정리한 MP모델에 넣은 걸 result에 작업
        screen = np.ones((screen_h, screen_w, 3), dtype=np.uint8) * 255
        # screen은 가로, 세로, 3채널에 1을 넣고, 타입은 넘파이 unit8인데, 여기 255를 곱함(흰색)

        if results.multi_face_landmarks:    # result에 얼굴 주요지표가 들어간다면
            for face_landmarks in results.multi_face_landmarks:     # 각 얼굴 지표별로
                left_eye_top = face_landmarks.landmark[159].y       # 왼쪽 위 눈꺼풀
                left_eye_bottom = face_landmarks.landmark[145].y    # 왼쪽 아래 눈꺼풀
                forehead_y = face_landmarks.landmark[10].y
                chin_y = face_landmarks.landmark[152].y
                face_height = abs(chin_y - forehead_y)
                eye_openness = abs(left_eye_bottom - left_eye_top)  # 눈 떳는지 여부
                eye_openness_normalized = eye_openness / face_height

                #눈 깜빡임
                if open_ref is not None and eye_openness_normalized < open_ref * 0.5 :
                    blink_frame_count +=1       # 프레임 카운트 추가
                    if blink_frame_count >= blink_threshold:
                        bBlink = 1              # 감은 상태
                        was_closed = True     # 감은 횟수
                else:
                    if was_closed:
                        blinked_count +=1
                        was_closed = False
                    blink_frame_count = 0       # 프레임 카운트
                    bBlink = 0                  # 감은 상태

                if open_ref is not None:
                    print(f"left_top :{left_eye_top:.4f}, left_bottom :{left_eye_bottom:.5f}, eye_openness_normalized: {eye_openness_normalized:.5f}, open_ref: {open_ref:.4f} bBlink: {bBlink}, frame_count: {blink_frame_count}")
                else:
                    print(f"left_top :{left_eye_top:.4f}, left_bottom :{left_eye_bottom:.5f}, eye_openness_normalized: {eye_openness_normalized:.5f}, bBlink: {bBlink}, frame_count: {blink_frame_count}")
                
                if show_face_mesh and face_mesh_frame is not None:  # 메쉬를 받기로 했고, 들어온다면
                    mp_drawing.draw_landmarks(      # 주요 지점에서 이하를 mp_drawing에 넣는다
                        image=face_mesh_frame,      # 그림 그릴 대상은 얼굴프레임
                        landmark_list=face_landmarks,   # 주요 지점 리스트 = 얼굴 주요 지점
                        connections=mp_face_mesh.FACEMESH_TESSELATION,  # 연결(선) = 얼굴 메쉬 중 테셀레이션(겹치지 않게 공간 채움)
                        landmark_drawing_spec=None, #랜드마크(점)를 어떻게 그릴지 = 기본
                        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
                    )   # 선 어떻게 그릴지 = mp스타일에서 기본 테셀레이션 스타일
                    mp_drawing.draw_landmarks(      #주요 지점에서 이하를 mp_drawing에 가져간다
                        image=face_mesh_frame,      # 그릴 대상 = 얼굴 프레임
                        landmark_list=face_landmarks,   # 주요 지점 리스트 = 얼굴 주요 지점
                        connections=mp_face_mesh.FACEMESH_IRISES,   # 선들 = mp_얼굴 메쉬에서 홍채
                        landmark_drawing_spec=None, # 주요 지점(점) 그리는 설정 = 기본
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0,255,0), thickness=1)
                    )   # 선 어떻게 그릴지 = mp스타일에서 이 색으로 그려라
                left_iris = face_landmarks.landmark[468]    # 왼쪽 홍채 = 주요지표 중 468번
                right_iris = face_landmarks.landmark[473]   # 오른쪽 홍채 = 주요지표 중 473번
                nose_tip = face_landmarks.landmark[1]       # 코 끝(기준점) = 얼굴 주요지표 중 1번

                eye_x = (left_iris.x + right_iris.x) / 2    # 눈동자 시선 중 x좌표 중간값
                eye_y = (left_iris.y + right_iris.y) / 2    # 눈동자 시선 중 y좌표 중간값

                dx = eye_x - nose_tip.x     # 시선 좌우 상대좌표 (코끝 기준으로 얼마나 벗어났는가)
                dy = eye_y - nose_tip.y     # 시선 상하 상대좌표 (코끝 기준...)

                gaze_x = int((0.5 + dx * 5) * screen_w) # 상대좌표를 키우고(*5) 0.5(가운데)를 더함, 상대좌표가 음수면 나가버리니까
                gaze_y = int((0.5 + dy * 5) * screen_h) # 상대좌표를 키우고 가운데 위치를 지정. 가운데 기반으로 유도

                gaze_x = np.clip(gaze_x, 0, screen_w - 1)   # 자르기(현재값, 최소값, 최대값)
                gaze_y = np.clip(gaze_y, 0, screen_h - 1)   # 자르기(현재값, 최소값, 최대값)

                if not calibration_complete:    # 칼리브레이션이 안된다면
                    if calibration_step < 4:    # 아직 진행 중 이라면
                        # 보정용 십자 표시
                        draw_cross(screen, corner_points[calibration_step], 30, (0, 0, 255), 2)
                        # 십자가를 그린다(배경에, 지정한 코너포인트[각 순서], 크기, 색, 두께(-1 = 채운다))
                        font = cv2.FONT_HERSHEY_SIMPLEX                     # 폰트
                        text = instructions[calibration_step]               # 어떤 문구? = 위에 지정한 문구(페이지 별)
                        (tw, th), _ = cv2.getTextSize(text, font, 0.8, 2)   # 텍스트 가로, 세로, 최저 높이 = 텍스트 크기(내용, 폰트, 크기, 두께 )
                        tx = (screen_w - tw) // 2   # 텍스트 가로 좌표
                        ty = screen_h // 2          # 텍스트 세로 좌표
                        cv2.putText(screen, text, (tx, ty), font, 0.8, (0, 0, 0), 2)
                        # 텍스트를 그려라(배경에, 글자를, 위치, 폰트, 크기, 색상, 두께)
                else:   # 칼리브레이션 완료 됫다면
                    # 눈 위치를 보정된 화면 좌표로 매핑
                    xs, ys = zip(*calibration_points)   # 눈 위치 리스트를 unpack
                    min_x, max_x = min(xs), max(xs)     # 최소 최대 x좌표 위치값
                    min_y, max_y = min(ys), max(ys)     # 최소 최대 y좌표 위치값

                    range_x = max_x - min_x # 범위 = 최대값 - 최소값
                    range_y = max_y - min_y # 범위 = 최대값 - 최소값

                    dx = eye_x  # dx = 눈 x 좌표
                    dy = eye_y  # dy = 눈 y 좌표

                    if range_x == 0 or range_y == 0: #만약 범위가 0이라면
                        mapped_x, mapped_y = screen_w // 2, screen_h // 2
                        # 최종 위치 = 화면 가운데
                    else:   #range가 0이 아니라면
                        mapped_x = int((dx - min_x) / range_x * screen_w)
                        mapped_y = int((dy - min_y) / range_y * screen_h)
                        # 각 값 = (눈 좌표 - 최소값) / x 범위 * 전체 너비(높이)

                    mapped_x = np.clip(mapped_x, 0, screen_w - 1)
                    mapped_y = np.clip(mapped_y, 0, screen_h - 1)
                        # 만약에 보저오딘 크기가 넘으면 잘라

                    if prev_x is not None and prev_y is not None:   #처음 시작할 때 이전 좌표가 없기 때문에, 있을 때에만 실행
                        mapped_x = int(alpha * mapped_x + (1 - alpha) * prev_x) #좌표 = 조정값 * 위치 + (1-조정값) * 이전 값
                        mapped_y = int(alpha * mapped_y + (1 - alpha) * prev_y) 

                    prev_x, prev_y = mapped_x, mapped_y     # 이전 값 = 현재 값

                    cv2.circle(screen, (mapped_x, mapped_y), 20, (0, 0, 255), -1)
                    blink_text = f"Closed Count: {blinked_count}"
                    cv2.putText(screen, blink_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

                    # 원을 그려라, 화면에, 좌표, 크기, 색, 두꼐(채운다)
                    if not stop_event.is_set():     # 안멈추면
                        q.put({
                            "type": "response",
                            "data": {
                                "quiz_id": 1,
                                "screen_w": screen_w,
                                "screen_h": screen_h,
                                "x": mapped_x,
                                "y": mapped_y,
                                "blink": bBlink,
                                "state": 100
                            }
                        })

        key = cv2.waitKey(1) & 0xFF # key는 1밀리초동안 기다리고 8비트(ASCII) 마스킹 함
        if key == ord('w') and not calibration_complete and calibration_step < 4:
            # w를 눌렀고, 칼리브레이션이 안끝났다면
            calibration_points.append((eye_x, eye_y))   # 칼리브레이션 포인트에 눈 위치 추가
            calibration_eye_open_list.append(eye_openness_normalized)
            calibration_step += 1   # 단계에 1 추가
            if calibration_step == 4:   # 만약 단계가 다 되었다면
                open_ref = np.mean(calibration_eye_open_list)
                calibration_complete = True #칼리브레이션 끝 

        if key == ord('q'): # q누르면
            if stop_event is not None:  # stop_event가 들어오면
                print("🛑 Gaze Estimation 종료 신호 전송")  # 출력
                stop_event.set()        # stop_event 실행
            break# 종료

        cv2.imshow("Gaze Estimation", screen)   #"Gaze..." 이라는 스크린을 켜줘
        if show_face_mesh and face_mesh_frame is not None:
            # 만약 얼굴메쉬가 켜져있다면
            cv2.imshow("Face Mesh View", face_mesh_frame)
            # 얼굴 보기 를 face_mesh를 Face_Mesh...로 삽입

    cap.release()   # 캡쳐 멈춰
    cv2.destroyAllWindows() # 모든 창 종료