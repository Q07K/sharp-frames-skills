<p align="center">
  <img src="assets/brand/sharp-frames-mascot-simple.png" alt="각진 안경을 쓴 Sharp Frames 마스코트" width="240" />
</p>

# Sharp Frames

**AI가 만든 코드를, 사람이 이해하고 계속 고칠 수 있게.**

Sharp Frames는 AI가 개발할 때 **기능 완성·기존 코드 재사용·검증**을 함께 챙기도록 돕는
개발 스킬 모음입니다. 새 기능 구현, 버그 수정, 리팩터링, 계획과 리뷰에 맞는 스킬을 골라 씁니다.

기능이 돌아가도 인증·업무 규칙·DB 처리가 한곳에 섞이거나 같은 판단이 여러 곳에 반복되면
다음 변경이 어려워집니다. AI에게 매번 이 기준을 길게 설명하지 않고, **무엇을 재사용하고,
어디를 나누고, 어떤 동작을 확인할지** 함께 판단하게 하려고 만들었습니다.

## 원하는 작업만 짧게 말하세요

새 프로젝트라면:

```text
$sharp-frames-development FastAPI로 로그인과 게시글 CRUD API 만들어줘.
```

이미 코드가 있다면:

```text
$sharp-frames-development 이 코드 정리해줘.
```

재사용·책임 분리·테스트 순서를 매번 설명할 필요는 없습니다. 스킬이 코드와 기존 계약을
읽고 작업에 맞게 적용합니다. 꼭 지켜야 하는 사업 규칙이나 배포 조건만 덧붙이세요.
Claude Code에서는 `$` 대신 `/sharp-frames-development`로 호출합니다.

## 같은 게시글 API를 만드는 세 가지 경로

짧은 요청을 **독립 작업 폴더·가상환경·새 대화**에서 실제로 실행했습니다.
로그인과 게시글 CRUD를 만들고 SQLite에 저장합니다. 긴 기능 명세나 원하는 폴더 구조는
주지 않았습니다. 준비된 Python 실행기와 설치 패키지는 공통으로 안내했습니다.

```text
빈 프로젝트 ── 스킬 없이 개발 ── A: 처음 만든 코드
                                 └── 스킬로 정리 ── C: 기존 코드 개선
별도 빈 프로젝트 ── 처음부터 스킬로 개발 ── B: 새 개발 결과
```

### 1. 같은 프롬프트에 스킬을 붙이면

**스킬 미사용 · A**

```text
FastAPI로 로그인과 게시글 CRUD API 만들어줘.
```

**스킬 사용 · B**

```text
$sharp-frames-development FastAPI로 로그인과 게시글 CRUD API 만들어줘.
```

제품 요청은 같고 스킬 설치·호출 여부만 다릅니다. 실제 실험은 Claude Code의 `/` 호출로
진행했습니다. 두 조건 모두 같은 환경 안내를 추가했고, 이전 예제·상대 코드·외부 검사는
제공하지 않았습니다.

| 실제 관측 | A · 미사용 새 개발 | B · 처음부터 스킬 사용 |
| --- | --- | --- |
| 로그인·게시글 CRUD | 구현·외부 흐름 통과 | 구현·외부 흐름 통과 |
| 인증·라우터·DB 분리 | 이미 분리함 | 분리함 |
| 작성자 권한 판단 | 공통 함수 사용 | 공통 함수 사용 |
| 검사 구성 | API 검사 한 파일 | 인증·게시글 검사와 케이스 표 |
| 앱 구성 | 모듈의 앱 + 환경 설정 | DB 경로를 받는 앱 생성 함수 |

**최초 공통 흐름 검사에서는 동률이었습니다.** 이후 원본의 저장 완료 시점 문제를
발견해 아래에 추가 검사 결과를 남겼습니다. 미사용 결과도 모듈화와 권한 검사를 갖췄으며,
폴더나 테스트 수가 많다는 이유로 품질 우위를 주장하지 않습니다.

### 2. 먼저 만든 코드를 스킬로 정리하면 · A → C

A를 그대로 세 번째 공간에 복사하고 새 대화에서 요청했습니다.

```text
$sharp-frames-development 이 코드 정리해줘.
```

**정리 전 · A** — 이미 역할별 파일이 있는 상태입니다.

```text
app/
├── main.py
├── db.py
├── schemas.py
├── security.py
└── routers/
    ├── auth.py
    └── posts.py
tests/
└── test_api.py
```

**정리 후 · C** — 폴더는 유지하고 파일 사이의 책임을 정리했습니다.

```text
app/
├── main.py
├── db.py            # 공통 DB 의존성·연결 수명 관리
├── schemas.py
├── security.py      # 공통 인증 실패 응답
└── routers/
    ├── auth.py      # 공통 DB·인증 응답 재사용
    └── posts.py     # 공통 DB 재사용
tests/
└── test_api.py      # 기존 검사 + commit 실패 회귀
```

예를 들어 DB 의존성은 원래 인증·게시글 파일과 인증 처리에 각각 선언되어 있었습니다.

```python
# A: auth.py와 posts.py에서 각각 선언
Db = Annotated[sqlite3.Connection, Depends(get_db)]
```

정리 후에는 DB 모듈의 선언을 세 곳에서 함께 사용합니다.

```python
# C: db.py에서 한 번 선언
DbConnection = Annotated[sqlite3.Connection, Depends(get_db, scope="function")]
```

공통 선언으로 commit을 응답 전에 마치도록 맞추고, 초기화 연결도 명시적으로 닫습니다.
로그인 실패 응답은 기존 인증 오류 함수를 재사용합니다. 폴더 재편 없이도 고칠 곳이 줄었습니다.
[실제 정리 전 코드](examples/fastapi-short-prompt/without-skill/app/db.py)와
[정리 후 코드](examples/fastapi-short-prompt/refactored/app/db.py)를 비교할 수 있습니다.

기존 HTTP 흐름과 OpenAPI는 유지했습니다. **commit 실패를 성공 응답으로 내보내던 경우는
500으로 고쳤습니다.** 이 오류 동작 수정은 단순한 코드 이동과 구분합니다.

### 3. 처음부터 스킬로 개발하면 · B

B는 A를 정리한 코드가 아니라, **빈 프로젝트에서 같은 개발 요청으로 만든 별도 결과**입니다.
초기부터 앱 생성·DB·인증·게시글을 나누고, 인증과 게시글 검사를 따로 구성했습니다.
공통 초기화 파일과 입력·실행 문서는 아래 트리에서 생략했습니다.

```text
app/
├── main.py           # 앱 생성·라우터 연결
├── db.py             # 연결·스키마
├── schemas.py        # 요청·응답 계약
├── auth.py           # 세션·인증·회원 라우터
└── posts.py          # 게시글 CRUD·작성자 판단
tests/
├── conftest.py
├── test_auth.py
├── test_posts.py
└── CASE_MATRIX.md    # 기능·역할·검사의 연결
```

예를 들어 [앱 생성 함수](examples/fastapi-short-prompt/with-skill/app/main.py)는 DB 경로와
토큰 수명을 받아 인스턴스별로 설정합니다. 아래는 실제 생성 코드의 일부입니다.

```python
def create_app(database_path: str, token_ttl: timedelta = DEFAULT_TOKEN_TTL) -> FastAPI:
    init_schema(database_path)
    app = FastAPI(title="Board API")
    app.state.database_path = database_path
    app.state.token_ttl = token_ttl
    app.include_router(auth.router)
    app.include_router(posts.router)
    return app
```

테스트에서는 별도 DB 경로로 앱을 만들 수 있습니다. 이 구조를 스킬의 고정 템플릿으로
강제한 것은 아닙니다. A의 작성자 필터와 B의 응답 모델 등 자율적으로 선택한 기능·계약은
서로 다르므로 두 새 개발 결과를 API 전체가 같은 구현으로 보지는 않습니다.

### 실제 확인한 결과

| 검사 | A · 미사용 | C · A를 정리 | B · 처음부터 사용 |
| --- | --- | --- | --- |
| 최초 공통 HTTP 흐름·안전성 관측 | 6/6 통과 | 6/6 통과 | 6/6 통과 |
| A의 OpenAPI 계약 비교 | 원본 고정 | 일치 | 별도 API라 비교하지 않음 |
| 수정하지 않은 A의 기존 검사 | 8/8 통과 | 8/8 통과 | 별도 계약이라 비교하지 않음 |
| 성공 응답 직후 강제 종료·재시작 (사후 10회) | **0/10 통과** | **10/10 통과** | **10/10 통과** |

공통 흐름은 로그인·CRUD, 잘못된 비밀번호, 익명·다른 작성자·위조 토큰 거부 후 데이터 보존,
재시작 후 게시글 보존입니다. **재실행에서는 A의 성공 응답 직후 강제 종료 시 글이
저장되지 않는 경합을 발견했습니다.** Windows에서 같은 검사를 10회 반복한 결과가 마지막
행입니다. 생성 결과는 수정하지 않았습니다. 정리 과정에서 발견한 commit 실패 검사도
A에서는 실패하고 C에서는 통과했습니다. 이 추가 발견들은 사전에 고정한 A/B 점수와 구분합니다.

조건별 1회이며 C는 A에서 파생됐습니다. 같은 OS·계정을 쓴 실험으로, 일반적인 품질·속도
향상을 입증하지 않습니다. [세 프로젝트 실행하기](examples/fastapi-short-prompt/README.md) ·
[전체 요청·검사·로그·독립 범위](evals/short-prompt/README.md)

이전 [상세 요구사항 기반 독립 비교](evals/board-independent/README.md)와
[한 작성자의 설명용 before/after](examples/fastapi-board/README.md)도 성격을 구분해 보존합니다.

## 설치하고 사용하기

### Codex

`skills/`에서 사용할 폴더 전체를 개인용 `~/.agents/skills/` 또는 프로젝트의
`.agents/skills/` 아래에 복사합니다. 전체 메뉴는 12개입니다.

```text
$sharp-frames-help
$sharp-frames-review 현재 변경을 검토해줘. 코드는 수정하지 마.
```

### Claude Code

스킬 폴더 전체를 `~/.claude/skills/` 또는 프로젝트의 `.claude/skills/` 아래에 복사합니다.
예를 들어 `.claude/skills/sharp-frames-review/SKILL.md`를 설치합니다.

```text
/sharp-frames-help
/sharp-frames-review 현재 변경을 검토해줘. 코드는 수정하지 마.
```

플러그인 설치는 실제 등록된 `/plugin-name:skill-name`을 사용합니다.
[Claude Code 공식 안내](https://code.claude.com/docs/en/skills)를 참고하세요.
같은 이름의 기존 스킬은 변경 내용을 확인하고 교체합니다. 설치가 바로 노출되지 않으면
새 대화에서 발견 여부를 확인합니다. 이전 `maintainable-development`는
`sharp-frames-development`로 교체하며, 과거 평가 기록의 이름·해시는 당시 상태를 유지합니다.

자연어 자동 선택은 호스트와 다른 설치 스킬의 영향을 받습니다. Superpowers나 기본
`/code-review`와 역할이 겹칠 수 있으며, 직접 호출해도 다른 워크플로의 동시 선택을
막지는 않습니다. 선택 우선순위는 보장하지 않습니다.
[실제 호스트 평가와 관측 결과](evals/routing/README.md)를 별도로 공개합니다.

## 목적에 맞는 스킬 고르기

<!-- sharp-frames-catalog:start -->
| Codex | Claude Code | 역할 | 소스 수정 |
| --- | --- | --- | --- |
| `$sharp-frames-development` | `/sharp-frames-development` | TDD 기반 기능 구현·버그 수정·일반 리팩터링 | 요청 범위 내 수정 |
| `$sharp-frames-brainstorm` | `/sharp-frames-brainstorm` | 기능 목표·대안·범위·수용 기준 구체화 | 읽기·보고 |
| `$sharp-frames-plan` | `/sharp-frames-plan` | 재사용·변경 순서·검증·마이그레이션 계획 | 읽기·보고 |
| `$sharp-frames-test` | `/sharp-frames-test` | 테스트 설계·케이스 관리·페르소나 흐름·회귀 검증 | 요청 범위 내 수정 |
| `$sharp-frames-versions` | `/sharp-frames-versions` | 최신 공식·커뮤니티 근거로 버전 유지·업데이트 영향 판단 | 읽기·보고 |
| `$sharp-frames-review` | `/sharp-frames-review` | 변경 diff·커밋·브랜치·PR 리뷰 | 읽기·보고 |
| `$sharp-frames-audit` | `/sharp-frames-audit` | 프로젝트 전체·하위 시스템 진단과 우선순위 | 읽기·보고 |
| `$sharp-frames-debt` | `/sharp-frames-debt` | 신규·기존·해소·미확인 기술 부채 정리 | 읽기·보고 |
| `$sharp-frames-gain` | `/sharp-frames-gain` | 개선 전후 효과·근거·비용·남은 위험 비교 | 읽기·보고 |
| `$sharp-frames-map` | `/sharp-frames-map` | 프로젝트 흐름·정책 소유자·재사용 후보 파악 | 읽기·보고 |
| `$sharp-frames-improve` | `/sharp-frames-improve` | 선택한 지적·개선 항목 적용과 검증·효과 정리 | 요청 범위 내 수정 |
| `$sharp-frames-help` | `/sharp-frames-help` | 명령 목록·선택 기준·사용 예시 | 읽기·보고 |
<!-- sharp-frames-catalog:end -->

위 Claude Code 표기는 스킬 폴더를 직접 설치한 경우입니다.
목표가 명확하면 `development`로 바로 구현하고, 목표가 불명확하면 `brainstorm`,
여러 모듈의 변경 순서가 필요하면 `plan`을 선택합니다. 세 단계를 매번 거칠 필요는 없습니다.

리뷰·진단만 요청하면 구현을 고치지 않습니다. `improve`나 구현을 요청하면 해당 범위를
수정하고 검증합니다. 구현에는 TDD와 회귀·사용자 흐름 확인이 포함되며,
별도 케이스 설계·관리는 `test`를 사용할 수 있습니다. 파일·보고서·부채 대장은 요청이나
기존 저장소 규칙에 따라 저장합니다.

[명령 선택과 상세 예시](docs/commands.md) · [기능 개발 흐름](docs/feature-workflow.md) ·
[테스트와 검증 기준](docs/testing-workflow.md)

## 검증 상태와 기여

**실험 단계입니다.** 짧은 요청 비교는 조건별 1회이며 최초 흐름 통과 후 원본의 저장 경합을 발견했습니다. 별도의 초기
FastAPI·SQLite 스킬 사용/미사용 비교도 각 9개 결과가 모두 외부 검사를 통과해
일관된 품질 우위를 확인하지 못했습니다. [기존 비교 결과](evals/results/fastapi-2026-10-20.md),
[기능별 수용 검사](evals/suite/README.md), [탐색·계획·버전 검사](evals/discovery/README.md),
[TDD·테스트 무결성 검사](evals/tdd/README.md)의 범위와 한계를 함께 공개합니다.

```sh
python -m pip install -r requirements-dev.txt
python tools/check_repository.py
python -m unittest discover -s tests -v
```

위 명령은 패키지 형식·링크·평가 입력과 기본 fixture, 보조 도구를 검사합니다.
앞의 게시글 API 검사와 실제 호스트 자동 선택 평가는 따로 실행합니다.
Windows에서 `python`이 실행되지 않으면 [실행기·uv 대체 명령](docs/python-runtime.md)을 참고하세요.
명령 표는 help의 catalog가 기준이며 `python tools/render_catalog.py --write`로 갱신합니다.

스킬은 프로젝트 고유 정책·CI·사람의 리뷰를 대신하거나 배포·외부 변경 권한을 추가하지 않습니다.
[평가 방법](evals/README.md) · [첫 비교와 한계](evals/results/iteration-1.md) ·
[기여 방법](CONTRIBUTING.md) · [설계 근거](docs/sources.md) ·
[다른 스킬과 비교한 결정](docs/skill-landscape.md)

## License

MIT. [LICENSE](LICENSE)를 참고하세요. 특정 회사의 공식 스킬이나 인증된 구현은 아닙니다.
