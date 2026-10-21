# Claude Code 호출 안내·스킬 공존 확인

실행일: 2026-10-21(KST). Claude Code 2.1.292, 세션이 보고한 모델
`claude-opus-5-5`, Superpowers 7.0.0에서 확인했습니다. 모델은 별도로 지정하지 않았습니다.
이는 호출·선택 스모크 검사이며 구현 품질·생산성 비교 실험이 아닙니다.

## 자연어 선택

`triggers.json`의 아래 네 query를 조건별 한 번씩, 총 8개의 독립 복사본과 새 대화에서
실행했습니다. 각 입력에는 원래 shop fixture 복사본과 배포 스킬만 제공했고, 기대 대상과
should_trigger·이전 출력은 제공하지 않았습니다.

| 사례 ID | 단독 조건의 첫 Skill 호출 | 공존 조건의 첫 Skill 호출 |
| --- | --- | --- |
| `brainstorm-positive` | `sharp-frames-brainstorm` | `sharp-frames-brainstorm` |
| `plan-positive` | `sharp-frames-plan` | `sharp-frames-plan` |
| `review-positive` | `sharp-frames-review` | `sharp-frames-review` |
| `development-01` | `sharp-frames-development` | `sharp-frames-development` |

각 실행에서 이후 추가 Skill 호출은 없었습니다. 공존 조건의 시작 훅은 네 번 모두
exit code 0으로 성공했고, using-superpowers와 1% 지침이 포함된 문맥을 주입했습니다.
따라서 이 표본에서는 Superpowers가 Sharp Frames보다 먼저 선택된다는 추측을 재현하지
못했습니다. 단독·공존의 대상 선택 결과는 동률입니다. 시작 훅의 문맥 주입과 이후
명시적인 Skill 도구 호출은 서로 구분했습니다.

공통 옵션은 `--print --output-format stream-json --verbose
--no-session-persistence --permission-mode dontAsk --tools Read,Glob,Grep,Skill
--strict-mcp-config --setting-sources project`입니다. 공존 조건에만 실제 설치된
Superpowers 7.0.0 경로를 `--plugin-dir`로 추가했습니다. 사용자 전역 설정은 변경하지
않았으며, init 이벤트에서 스킬·플러그인 구성과 기본 `code-review`의 노출을 확인했습니다.

**읽기·선택 검사라는 제한이 있습니다.** 파일 수정·셸·테스트 실행 도구를 제공하지
않았습니다. 구현 사례 두 결과 모두 수정·테스트를 못 했다고 보고하고 변경안만
제시했습니다. 선택 확인과 구현 완료는 다르며, 이 두 결과를 구현 성공으로 세지 않습니다.
모든 실행의 fixture 파일 집합·내용이 원본과 일치했습니다.

## 직접 호출한 help

같은 새 이름·catalog·호스트·도구 조건에서 기존/수정 help를 각각 한 번
`/sharp-frames-help`로 호출했습니다. 기존 help의 구현 스킬 참조는 새 이름으로 맞췄고,
나머지는 변경 전 본문을 사용했습니다.

| 확인 항목 | 기존 help | 수정 help |
| --- | --- | --- |
| 명령 표 | 12개 모두 접두어 없는 이름 | 12개 모두 `/sharp-frames-…` |
| 본문 예시 | `/`로 변환해 출력 | `/`로 변환해 출력 |
| 도구 사용 | catalog 읽기 1회 | catalog 읽기 1회 |
| 프로젝트 검사·파일 수정 | 없음 | 없음 |

예시 변환은 이 비교에서 동률입니다. 수정 help의 표에는 직접 호출 문법이 나타났습니다.
각 한 번의 출력으로 지속적인 개선율을 주장하지 않습니다.

별도의 예비 실행 1회에서는 변경 전 help가 `$` 예시를 출력했습니다. 이 예비 입력에는
이전 구현 스킬 이름도 남아 있었으므로 위의 동일 이름 비교에 합치지 않았습니다.
예비 결과도 증빙에 포함하며, 기존 help가 항상 `$`만 출력한다고 일반화하지 않습니다.

## Windows 실행 안내와 패키지 검사

WindowsApps의 `python --version` 실행 실패를 확인했습니다. 설치된 Python 3.13.8의
절대 경로로 두 helper의 `--help`가 실행됐고, gain helper는 uv와 기존 인터프리터를
지정한 대체 명령으로도 실행됐습니다. 두 helper는 PyYAML 없이 실행됩니다.
패키지 검사는 `uv run --with-requirements requirements-dev.txt --python <기존-인터프리터>
python tools/check_repository.py`로 12개 스킬·2개 행동 평가 입력·18개 선택 사례와
원래 fixture를 확인했고, 보조 도구 회귀 테스트 8개가 통과했습니다.

스킬 형식 검사 도구가 Windows 기본 cp949로 help를 읽다 중단된 실행은 UTF-8 모드로
재실행해 통과했습니다. 이는 도구 실행 환경 문제이며 행동 평가 실패를 숨긴 것이 아닙니다.
`py -3`는 이 PC에 없어 실행하지 않았습니다. 런타임이 전혀 없는 환경에서 에이전트가
수동 확인으로 전환하는 행동은 이번에 평가하지 않았습니다.

## 증빙과 미확인 범위

[실행 증빙](claude-code-2026-10-21-evidence.zip)과
[압축 파일 SHA-256](claude-code-2026-10-21-archive-sha256.txt)을 공개합니다.
압축 파일에는 입력 fixture, 평가 시점 스킬과 LF 기준 지문, 비교용 기존 help,
실행 스크립트, 사례별 init 메타데이터·도구 호출·최종 출력·CLI 시간/토큰 정보가 있습니다.
개인 경로는 자리표시자로 바꿨으며 thinking·외부 플러그인의 본문은 포함하지 않았습니다.
시작 훅은 성공 상태·문맥 지문과 해당 지침 포함 여부를 기록했습니다.
전체 원시 JSONL은 로컬 `evals/runs/claude-compat-2026-10-21/`에 보관했습니다.

평가 복사본을 만든 뒤 debt/gain의 Windows 세부 안내를 연결된 reference로 옮겼습니다.
위 자동 선택 대상 스킬의 name/description과 평가한 help는 그대로이며, 해당 두 스킬의
실제 에이전트 동작까지 이 평가가 입증하는 것은 아닙니다.

추가한 18개 선택 사례 중 네 개의 긍정 사례만 두 조건에서 실행했습니다. 나머지 긍정·부정
사례, 자연어 help 선택, 직접 호출한 review, 플러그인 namespace 호출, 다른 모델·호스트,
Codex의 실제 자동 선택은 미확인입니다. 시간·토큰 메타데이터가 있어도 작은 단일 표본과
캐시·출력 차이로 생산성·비용 개선을 주장하지 않습니다. 원래 fixture·grader와 과거
평가 해시는 변경하지 않았습니다.
