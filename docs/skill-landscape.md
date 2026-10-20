# 기능별 스킬 조사와 반영 결정

조사일: 2026-10-20. 사용자가 지정한 Ponytail을 중심으로 아래 원본 저장소의 실제
스킬을 읽었습니다. 인기·기능 목록은 효과 입증과 구분합니다. 각 링크는 조사한 리비전에
고정했습니다. 이 문서는 선택 기준의 조사 기록이며 외부 원문이나 구현 코드를 배포하지 않습니다.

## Ponytail: 명령 목록과 작업 단위

[명령과 소개](https://github.com/DietrichGebert/ponytail/tree/09c434ab73ca43761c5d8b0c5d341926c2fba710),
[실제 스킬](https://github.com/DietrichGebert/ponytail/tree/09c434ab73ca43761c5d8b0c5d341926c2fba710/skills)
(MIT).

`ponytail` 외에 review, audit, debt, gain, help를 별도 기능으로 제공합니다.
리뷰는 변경과 관련 호출부를 읽고, audit은 프로젝트의 흐름과 부하를 먼저 파악합니다.
debt는 주로 `shortcut` 등으로 남긴 결정을 수집합니다. gain은 공개 벤치마크의 수치를
표시하며 현재 프로젝트의 절감량으로 오해하지 않도록 구분합니다.

**반영:** 명령별 목적·입력·수정 범위를 분리하고 도움말에서 선택할 수 있게 구성했습니다.
**확장:** 부채의 생성·증가·잔존·해소를 전후 비교로 구분하고, 현재 변경의 효과를 직접
설명하는 gain을 작성했습니다. 다른 프로젝트의 벤치마크 수치를 사용자의 성과로 쓰지 않습니다.

## Superpowers: 리뷰 수신과 검증의 분리

[리뷰 요청](https://github.com/obra/superpowers/tree/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/requesting-code-review),
[리뷰 수신](https://github.com/obra/superpowers/tree/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/receiving-code-review),
[완료 전 검증](https://github.com/obra/superpowers/tree/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/verification-before-completion)
(MIT).

리뷰의 범위와 요구사항을 명시하고, 외부 지적도 코드의 실제 상황과 대조하도록 구성합니다.
수정·완료 주장을 실제 검사 결과와 연결하는 워크플로가 있습니다.

**반영:** improve는 지적을 사실 확인한 뒤 선택 범위를 구현하고, 보고서는 실제 검사와
정적 추론을 구분합니다. **선택하지 않은 것:** 모든 작은 수정에 별도 검토자·전체 절차를
강제하는 방식. 작업 크기와 위험에 맞게 적용하고, 이미 요청한 일반 구현의 승인을 반복하지 않습니다.

## Trail of Bits: 맥락 구축·변경 검토·오탐 확인

[맥락 구축](https://github.com/trailofbits/skills/tree/5c99c03fb8a9ea568432ecbcba5d86e9f4ac2bf0/plugins/audit-context-building),
[변경 검토](https://github.com/trailofbits/skills/tree/5c99c03fb8a9ea568432ecbcba5d86e9f4ac2bf0/plugins/differential-review),
[오탐 확인](https://github.com/trailofbits/skills/tree/5c99c03fb8a9ea568432ecbcba5d86e9f4ac2bf0/plugins/fp-check)
(저장소 라이선스: CC BY-SA 4.0).

시스템의 가정·보장·호출 관계를 이해하는 단계와, 의심되는 문제를 판정하는 단계를
구분합니다. 변경의 영향과 실제 호출 경로·보호 장치를 확인하고 조사 범위의 한계를 남깁니다.

**반영:** map은 사실·재사용 후보를 설명하고 audit은 근거 있는 문제와 우선순위를 판정합니다.
review는 상위 검증을 확인한 뒤 문제를 보고합니다. 조사 깊이는 영역별로 공개합니다.
**선택하지 않은 것:** 전용 에이전트 이름·도구·보고 파일을 모든 호스트와 프로젝트에
필수로 만드는 방식. 구현은 이 패키지의 범위에 맞춰 독립적으로 작성했습니다.

## gstack: 목적별 워크플로와 실행 근거

[리뷰](https://github.com/garrytan/gstack/tree/c580561e8a5ac08e6cbdd52c7a0ce521ab6310a5/review),
[테스트 감사](https://github.com/garrytan/gstack/tree/c580561e8a5ac08e6cbdd52c7a0ce521ab6310a5/test-audit),
[회고](https://github.com/garrytan/gstack/tree/c580561e8a5ac08e6cbdd52c7a0ce521ab6310a5/retro)
(MIT).

리뷰·검사·회고 등의 작업을 구분하고, 비교 기준과 근거 종류를 명시합니다.
테스트 개수보다 지키는 계약과 실제로 검출할 회귀를 설명하도록 구성된 부분이 있습니다.

**반영:** 결과·변경 범위·검증 근거·남은 의무를 연결합니다. **선택하지 않은 것:**
자동 배포, 호스트별 상태 패널, 세션 수집과 텔레메트리, 일률적인 완성도 숫자, 방대한
상시 프롬프트. 현재 사용자의 유지보수 작업에 필요한 기능부터 제공합니다.

## 확장 목록

기본 구현 스킬과 review/audit/debt/gain/help를 연결하고, 재사용 탐색용 map과 선택한
지적을 구현하는 improve를 추가했습니다. 명령 목록은 [사용 안내](commands.md)의
정식 카탈로그에서 생성합니다.

후속 후보는 테스트 전략 진단과 구체적 리뷰 지적의 재검증입니다.
기능 탐색·계획·의존성 판단은 [추가 검토](feature-workflow.md)에 따라 별도 명령으로 확장했습니다.
현재 명령과 구분되는 실제 입력·산출물·평가 예제를 확보한 뒤 추가할 수 있습니다.
기능 개수 자체를 품질이나 비용 절감의 근거로 사용하지 않습니다.

기존 [FastAPI 비교](../evals/results/fastapi-2026-10-20.md)는 초기 구현 스킬 버전의 결과입니다.
이번 기능별 명령의 정확성·자동 선택·생산성 향상을 그 실험이 입증한다고 해석하지 않습니다.
