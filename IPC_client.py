import win32file
import win32pipe
import struct
import time

PIPE_NAME = r'\\.\pipe\unreal_pipe'
NOTIFY_STRUCT_FORMAT = '<BBBB'  # QuizID, SettingStart, Start, End

def main():
    print(f"🔗 [Client] 서버 파이프 연결 시도: {PIPE_NAME}")
    try:
        # 서버에 연결
        pipe = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,  # No sharing
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )
        print("✅ [Client] 서버 연결 성공")

    except Exception as e:
        print(f"❌ [Client] 서버 연결 실패: {e}")
        return

    try:
        # 보낼 데이터: (QuizID=1, SettingStart=1, Start=0, End=0)
        payload = struct.pack(NOTIFY_STRUCT_FORMAT, 1, 1, 0, 0)
        win32file.WriteFile(pipe, payload)
        print("📤 [Client] 데이터 전송 완료")

        # 서버 응답 대기
        response = win32file.ReadFile(pipe, 4096)[1]
        print(f"📨 [Client] 서버 응답 수신 (길이 {len(response)} bytes)")

        # 받아온 데이터 해석
        if len(response) >= 10:  # 예상되는 패킷 크기 (구조체 설계에 따라 다름)
            quiz_id, x, y, blink, state = struct.unpack('<BffBB', response[:10])
            print(f"📥 [Client] 응답 해석 → QuizID={quiz_id}, X={x:.2f}, Y={y:.2f}, Blink={blink}, State={state}")
        else:
            print("⚠️ [Client] 응답 데이터 크기가 예상보다 작음")

    except Exception as e:
        print(f"❌ [Client] 통신 중 오류 발생: {e}")
    
    finally:
        print("🔒 [Client] 파이프 연결 종료")
        win32file.CloseHandle(pipe)

if __name__ == "__main__":
    main()
