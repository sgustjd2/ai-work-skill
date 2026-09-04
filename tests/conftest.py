"""tests/ 공용 설정: templates/ 를 import 경로에 넣는다(훅·설치기는 표준 라이브러리 모듈)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
if str(TEMPLATES) not in sys.path:
    sys.path.insert(0, str(TEMPLATES))
