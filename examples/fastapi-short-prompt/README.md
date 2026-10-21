# 같은 짧은 요청, 두 가지 새 개발과 한 가지 코드 정리

2026-10-21에 독립 작업 공간과 새 Claude CLI 대화에서 실제 생성한 원본입니다.
제품 요청은 `FastAPI로 로그인과 게시글 CRUD API 만들어줘.`입니다.
준비된 런타임 안내 외에 상세 요구사항이나 정답 코드는 주지 않았습니다.

| 폴더 | 시작 | 용도 |
| --- | --- | --- |
| [without-skill](without-skill/README.md) | 빈 프로젝트 | 스킬 없이 먼저 만든 코드 A |
| [with-skill](with-skill/README.md) | 별도의 빈 프로젝트 + 스킬 | 같은 요청에 처음부터 스킬을 쓴 코드 B |
| [refactored](refactored/README.md) | A 원본 복사 + 스킬 | `이 코드 정리해줘.`로 정리한 코드 C |

B와 C는 다른 경로입니다. A→C만 기존 코드 정리의 before/after입니다.
생성 후 운영자가 코드를 고쳐 맞추지 않습니다. 환경 안내와 의존성 파일도 원본에 포함합니다.
각 하위 README는 개발 프로세스가 작성했으며 상위 문서와 외부 검사가 관측 근거입니다.

## 실행

원하는 하위 폴더로 이동해서 가상환경을 만듭니다.

```sh
python -m venv .venv
python -m pip install -r requirements.txt
python -m pytest -q
```

위 설치와 검사에서 `python`은 만든 가상환경의 인터프리터로 실행하세요.
Windows PowerShell은 `.venv/Scripts/python.exe`, macOS/Linux는 `.venv/bin/python`입니다.
Windows의 `python`이 Store 실행 파일이면 [실행기 안내](../../docs/python-runtime.md)를 참고하세요.

```sh
# A와 C
python -m uvicorn app.main:app

# B
python -m uvicorn app.main:create_app_from_env --factory
```

API 문서는 서버를 켠 뒤 `/docs`에서 볼 수 있습니다. 저장소는 SQLite이며 경로는
`DATABASE_PATH`로 바꿉니다. 생성된 프로젝트의 실행 예시는 Windows 준비 환경을 반영합니다.
개별 프로젝트의 기본값·필드·추가 기능은 서로 다를 수 있습니다.

[요청·분리 조건·고정 검사·증거와 한계](../../evals/short-prompt/README.md)를 함께 확인하세요.
