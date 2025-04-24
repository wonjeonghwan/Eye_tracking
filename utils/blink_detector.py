class BlinkDetector:
    def __init__(self, threshold_ratio = 0.5, blink_threshold = 4):
        self.threshold_ratio = threshold_ratio
        self.blink_threshold = blink_threshold
        self.blink_frame_count = 0
        self.blinked_count = 0
        self.blink_state = 0
        self.was_closed = False
        self.open_ref = None

    # 세팅 초기화
    def reset(self):
        self.blink_frame_count = 0
        self.blinked_count = 0
        self.blink_state = 0
        self.was_closed = False

    def update(self, eye_openness_norm, open_ref):
        if open_ref is None:
            return 0, self.blinked_count
        
        if eye_openness_norm < open_ref * self.threshold_ratio:
            self.blink_frame_count += 1
            if self.blink_frame_count >= self.blink_threshold:
                self.blink_state = 1
                self.was_closed = True
        
        else:
            if self.was_closed:
                self.blinked_count += 1
                self.was_closed = False
            self.blink_frame_count = 0
            self.blink_state = 0

        return self.blink_state, self.blinked_count
    