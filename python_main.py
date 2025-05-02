from calibration import run_full_calibration
from eye_tracking import run_eye_tracking

screen_w, screen_h = 2880, 1800
margin = 40

def main():
    print("1: 칼리브레이션")
    print("2: 시선 추적")
    print("0: 종료")

    while True:
        choice = input("모드를 선택하세요: ")
        if choice == "1":
            run_full_calibration(screen_w, screen_h, margin)
        elif choice == "2":
            run_eye_tracking(screen_w, screen_h)
        elif choice == "0":
            print("프로그램 종료")
            break
        else:
            print("잘못된 입력입니다.")

if __name__ == "__main__":
    main()
