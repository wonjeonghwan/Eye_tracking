## 📁 프로젝트 구조
- `main.py`: 실행 진입점 (눈 추적 또는 얼굴 메쉬 시각화)
- `eye_tracker.py`: 시선 추적(얼굴 기준 눈동자 위치 기반)
- `gaze_tracker.py`: 시선 추적(gaze estimation 기반)
- `face_mesh_viewer.py`: 얼굴 메쉬 시각화 전용 (개발용 참고)
- `requirements.txt`: Python 모듈 목록
- `ipc_listener.py` : 수신 확인용 파일
## 🛠 실행 방법
```bash
pip install -r requirements.txt
python main.py
```