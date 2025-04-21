# 📌 Git 브랜치 전략 (깨구락이 AI 팀)

## 📂 폴더 구조 요약
```
C:.
│  .gitignore
│  README.md
│
├─apps
│  ├─asset_generator     # 에셋 생성 담당
│  ├─eye_tracking        # 아이트래킹 담당
│  └─voice_quest         # 음성 퀘스트 담당
│
└─shared
        utills.py        # 공통 모듈 (전처리 전용)
```

## 🌳 브랜치 구조

| 브랜치 이름       | 설명                                       |
|------------------|--------------------------------------------|
| `main`           | 최종 릴리즈 / 게임 연동용 안정 브랜치         |
| `dev`            | 통합 개발 브랜치 (모든 기능 PR 대상)           |
| `voice_LLM`      | 음성 퀘스트 개발 (`apps/voice_quest`)         |
| `asset_generator`| 에셋 생성 기능 개발 (`apps/asset_generator`)   |
| `eye_tracking`   | 아이트래킹 퀘스트 개발 (`apps/eye_tracking`)   |

## 🔁 협업 플로우

1. 각자 본인 담당 브랜치에서 기능 개발  
2. 기능 완료 후 `dev` 브랜치로 PR 제출  
3. 통합 테스트 완료 후 `main` 브랜치에 머지  

## 🧹 기타 규칙

- `shared/utills.py`에는 **전처리 함수만 작성**  
- 공통 로직 아닌 기능별 코드는 **각 앱 폴더 내부에서 관리**  
- 테스트 파일은 다음 중 하나의 이름으로 작성:
  - `test.py`
  - `test.ipynb`
- PR 보낼 때 **공통 모듈 수정사항은 명확히 표기**
- 커밋 컨벤션:
  - `feat:` 기능 추가  
  - `fix:` 버그 수정  
  - `refactor:` 리팩터링  
  - `docs:` 문서 관련 수정