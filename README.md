# Eye Tracking Project

이 프로젝트는 MediaPipe 기반 눈동자 추적 데이터를 실시간으로 수집하고,
Unreal Engine과 연동하여 시선 기반 인터랙션을 구현할 수 있도록 설계되었습니다.

## 📁 프로젝트 구조
- `main.py`: 실행 진입점 (눈 추적 또는 얼굴 메쉬 시각화)
- `eye_tracker.py`: 시선 추적 및 캘리브레이션 처리
- `face_mesh_viewer.py`: 얼굴 메쉬 시각화 전용 (개발용 참고)
- `udp_sender.py`: Unreal로 UDP 통신 전송
- `.env`: IP와 PORT 설정값을 저장하는 환경설정 파일
- `requirements.txt`: Python 의존성 목록

## 🛠 실행 방법
```bash
pip install -r requirements.txt
python main.py
```

## ⚙️ 설정 사항 (Unreal 연동)
- `.env` 파일에 IP/PORT를 설정
```
UDP_IP=127.0.0.1
UDP_PORT=5050
```
- Python에서 지정한 IP/PORT와 Unreal에서 수신하는 포트가 일치해야 합니다.
- 기본 전송 포맷은 UDP (좌표 텍스트: "x,y\n") 형태입니다.