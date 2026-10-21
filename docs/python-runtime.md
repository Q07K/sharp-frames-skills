# Python 실행기와 Windows 대체 명령

문서의 `python`은 실행 가능한 Python 3 인터프리터를 뜻합니다. Windows의 실행 별칭이
WindowsApps 경로를 가리키지만 실행에 실패하면, 이미 설치된 실행기를 사용합니다.
`python --version`, `py -3 --version`, `uv --version` 중 사용할 명령을 확인하고,
모두 설치돼 있다고 가정하지 않습니다. 인터프리터의 절대 경로도 사용할 수 있습니다.

## 설치된 실행기 사용

Python 런처 `py`가 있다면 다음처럼 실행합니다.

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 tools/check_repository.py
py -3 -m unittest discover -s tests -v
```

uv가 있다면 저장소 루트에서 다음처럼 실행할 수 있습니다. 실행 환경에 없는 의존성은
다운로드될 수 있으므로 해당 환경의 네트워크·설치 권한을 따릅니다.

```powershell
uv run --with-requirements requirements-dev.txt python tools/check_repository.py
uv run --with-requirements requirements-dev.txt python -m unittest discover -s tests -v
```

이미 설치된 인터프리터를 지정하려면 `uv run --python <python.exe의-절대-경로> …`를
사용합니다. 새 런타임 설치나 운영체제 실행 별칭 변경을 필수 해결책으로 삼지 않습니다.

## 배포된 스킬의 보조 도구

`scan_debt.py`와 `compare_metrics.py`는 Python 표준 라이브러리만 사용합니다.
PyYAML은 이 저장소의 패키지 검사 의존성이며 두 보조 도구에는 필요하지 않습니다.
`<skill-dir>`은 사용 중인 스킬의 실제 설치 폴더로 바꿉니다.

```powershell
py -3 <skill-dir>/scripts/scan_debt.py --root <repo>
uv run python <skill-dir>/scripts/compare_metrics.py <before.json> <after.json>
```

debt 스캔은 선택 사항입니다. gain의 제공된 수치 비교에는 비교 도구를 사용하되,
실행기가 없으면 수동 확인 여부와 도구 미실행을 밝힙니다. 실행 실패를 후보 없음이나
검증 통과로 보고하지 않습니다.

[Python의 Windows 실행 안내](https://docs.python.org/3/using/windows.html) ·
[uv 스크립트·의존성 실행 안내](https://docs.astral.sh/uv/guides/scripts/).
