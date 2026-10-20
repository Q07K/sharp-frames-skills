# 설계 근거와 출처

2026-10-20에 공개 원문을 확인했습니다. 아래 자료는 아이디어와 판단 기준의 출처이며,
이 스킬의 효과를 입증하는 직접적인 실험 결과가 아닙니다. 기업 사례는 해당 조직의
자체 경험 보고이고, 제한된 연구 결과를 모든 프로젝트에 일반화하지 않습니다.

| 자료 | 반영한 판단 |
| --- | --- |
| [토스 Frontend Fundamentals](https://frontend-fundamentals.com/code-quality/code/) | 가독성·예측 가능성·응집도·결합도의 균형. 프론트엔드 구현을 백엔드에 그대로 복사하지 않음 |
| [우아한형제들: 아키텍처 규칙 자동 검사](https://techblog.woowahan.com/26835/) | AI 지침뿐 아니라 실행 가능한 검사, 기존 위반을 고려한 점진적 적용 |
| [카카오페이: SDD 실전기](https://tech.kakaopay.com/post/ifkakao-agentic-coding/) | 구현 전 의도·작업 범위 정리와 문서/단계 과잉의 비용 |
| [토스페이먼츠: MCP 구현기](https://toss.tech/article/tosspayments-mcp) | 많은 문서보다 필요한 맥락을 정확하게 찾는 방식 |
| [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) | 유용한 계약·타입·주석과 단순 코드 반복 설명의 구분 |
| [Google Code Review](https://google.github.io/eng-practices/review/reviewer/looking-for.html) | 설계·정확성·복잡성·테스트·이름·주석을 실제 변경에서 검토 |
| [Parnas, 1972](https://doi.org/10.1145/361598.361623) | 변경 가능한 설계 결정을 경계 안에 감추는 모듈화 |
| [Fowler: Refactoring](https://martinfowler.com/books/refactoring.html) | 동작을 보존하는 구조 개선과 기능 변경을 구분 |
| [Sandi Metz: The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction) | 잘못된 공통화보다 독립 정책의 분리가 나을 수 있음 |
| [Ousterhout: Modular Design](https://web.stanford.edu/~ouster/cgi-bin/cs190-winter18/lecture.php%3Ftopic%3DmodularDesign) | 분리된 파일 수보다 단순한 인터페이스가 감추는 복잡성에 집중 |
| [Stripe Minions, Part 2](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2) | 구현과 결정적인 자동 검사 단계를 연결하고 실행 근거를 확보 |
| [Spotify Honk verification](https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3) | 검사 통과와 기능 정확성은 다름. 범위 이탈과 검사 무력화도 확인 |
| [ETH: Evaluating AGENTS.md](https://www.sri.inf.ethz.ch/publications/gloaguen2026agentsmd) | 지침의 양을 성능으로 착각하지 않고 실제 비용·성공 여부로 평가 |
| [OpenAI: Skills and OSS maintenance](https://developers.openai.com/blog/skills-agents-sdk) | 저장소별 규칙과 반복 절차를 구분하고 필요한 참고 자료만 사용 |
| [OpenAI: Evaluating skills](https://developers.openai.com/blog/eval-skills) | 선택·실행·산출물·효율성을 구분해 평가 |

FastAPI 세부 사항은 [공식 문서](https://fastapi.tiangolo.com/),
트랜잭션은 [SQLAlchemy 문서](https://docs.sqlalchemy.org/en/20/orm/session_basics.html),
검증·마이그레이션은 [Pydantic 문서](https://docs.pydantic.dev/latest/migration/)를
실제 설치 버전과 대조합니다. 외부 Best Practices 문서의 버전 표를 그대로 강제하지 않습니다.
