# 눈 & 코 상대 시선 기준 좌표 계산
def compute_relative_gaze(eye_x, eye_y, nose_tip_x, nose_tip_y, screen_w, screen_h):
    dx = eye_x - nose_tip_x
    dy = eye_y - nose_tip_y

    gaze_x = int((0.5 + dx * 5) * screen_w)
    gaze_y = int((0.5 + dy * 5) * screen_h)

    gaze_x = max(0, min(gaze_x, screen_w -1))
    gaze_y = max(0, min(gaze_y, screen_h -1))

    return gaze_x, gaze_y

# 화면 좌표로 표현 및 보간
def map_calibrated_gaze(eye_x, eye_y, calibration_points, screen_w, screen_h, prev_x=None, prev_y=None, alpha = 0.5):
    if len(calibration_points) < 4:
        return screen_w // 2, screen_h //2

    xs, ys = zip(*calibration_points)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    range_x = max_x - min_x
    range_y = max_y - min_y

    if range_x == 0 or range_y ==0:
        mapped_x, mapped_y = screen_w //2, screen_h //2
    else:
        mapped_x = int((eye_x - min_x) / range_x * screen_w)
        mapped_y = int((eye_y - min_y) / range_y * screen_h)

    mapped_x = max(0, min(mapped_x, screen_w -1))
    mapped_y = max(0, min(mapped_y, screen_h -1))

    if prev_x is not None and prev_y is not None:
        mapped_x = int(alpha * mapped_x +(1 - alpha) * prev_x)
        mapped_y = int(alpha * mapped_y +(1 - alpha) * prev_y)

    return mapped_x, mapped_y