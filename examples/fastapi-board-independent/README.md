# 새 작업 공간에서 독립적으로 만든 두 게시글 API

동일한 요구를 새 Claude Code 세션 두 개에 제공해 각각 만든 원본 제출물입니다.
한쪽은 Sharp Frames가 없었고, 다른 쪽은 development만 설치해 직접 호출했습니다.
두 세션 모두 기존 예제·상대 코드·외부 검사를 보지 않고 자체 구현·검증을 마쳤습니다.
상세한 분리 범위와 한계는 [독립 실행 기록](../../evals/board-independent/README.md)을 참고하세요.

| 폴더 | 내용 | 동일한 외부 HTTP 계약 |
| --- | --- | --- |
| [without-skill](without-skill/README.md) | Sharp Frames 미사용 세션의 제출물 | 9/9 통과 |
| [with-skill](with-skill/README.md) | Sharp Frames 명시 호출 세션의 제출물 | 9/9 통과 |

회원가입·로그인·게시글 CRUD·작성자 권한·SQLite 저장과 세션 만료를 구현합니다.
동작 결과는 동률이며 두 구현 모두 모듈화·공유 권한 검사를 선택했습니다.
파일 수나 자체 검사 개수로 품질 우위를 주장하지 않습니다. 각 폴더의 코드·README·
자체 검사는 생성 세션의 원본이고, 이 상위 안내만 별도로 작성했습니다.

## 직접 실행

각 프로젝트 폴더에서 별도로 환경을 만들면 됩니다. 아래는 미사용 프로젝트의 예시입니다.
적용 프로젝트는 폴더를 `with-skill`로 바꾸고 다른 포트를 사용합니다.

```sh
cd examples/fastapi-board-independent/without-skill
python -m venv .venv
# Windows
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m uvicorn main:app --port 8001
```

macOS/Linux에서는 `.venv/bin/python`을 사용합니다. 두 프로젝트 모두 프로젝트 루트의
`main:app`으로 시작하며 `/docs`에서 회원가입→로그인→게시글 CRUD를 사용할 수 있습니다.
공통 요구는 각 폴더의 `REQUIREMENTS.md`, 환경 설정·자체 검사는 각 README를 참고하세요.
Python 3.12 이상이 필요하며 실제 비교 환경은 Windows·Python 3.13.8이었습니다.

외부 검사를 재실행하려면 저장소 루트에서 다음을 실행합니다.

```sh
python -X utf8 evals/board-independent/replay.py
```

이전 한 작성자의 구조 정리 예제는 [별도 폴더](../fastapi-board/README.md)에 남겨 두었습니다.
그 예제의 before/after를 이번 독립 실험의 원본 결과로 사용하지 않습니다.
