"""파서: frontmatter, 블록 타입, 인라인 run, 덱 슬라이드 분리·레이아웃 추론."""

from docgen import parse

DOC = """---
title: 테스트 설계서
doc_type: 설계서
version: 0.1
history:
  - { version: 0.1, date: 2026-09-04, author: 민현성, note: 초안 }
---
# 1. 개요
첫 문단이다. **굵게** 와 `코드` 와 [링크](https://example.com).

## 1.1 목적
- 항목 하나
- 항목 둘

| 항목 | 대안 A | 검토 의견 |
|---|---|---|
| 비용 | 낮음 | 적합 |

<!-- caption: 대안 비교표 -->

| 지표 | 값 |
|---|---|
| a | 1 |

```diagram
type: architecture
nodes:
  - { id: api, label: 요약 API }
```

![구성도 설명](images/x.png)

<!-- pagebreak -->

> 참고 박스
"""


def _types(blocks):
    return [b["type"] for b in blocks]


def test_frontmatter():
    doc = parse.parse_doc(DOC, is_text=True)
    fm = doc["frontmatter"]
    assert fm["title"] == "테스트 설계서"
    assert fm["doc_type"] == "설계서"
    assert isinstance(fm["history"], list) and fm["history"][0]["author"] == "민현성"


def test_block_sequence():
    blocks = parse.parse_doc(DOC, is_text=True)["blocks"]
    t = _types(blocks)
    assert t[0] == "heading" and blocks[0]["level"] == 1
    assert "paragraph" in t and "list" in t and "table" in t
    assert "diagram" in t and "image" in t and "pagebreak" in t and "blockquote" in t


def test_inline_runs():
    blocks = parse.parse_doc(DOC, is_text=True)["blocks"]
    para = next(b for b in blocks if b["type"] == "paragraph")
    runs = para["runs"]
    assert any(r.get("bold") for r in runs)
    assert any(r["kind"] == "code" for r in runs)
    assert any(r.get("link") for r in runs)


def test_table_and_caption():
    blocks = parse.parse_doc(DOC, is_text=True)["blocks"]
    tables = [b for b in blocks if b["type"] == "table"]
    assert parse.runs_text(tables[0]["header"][-1]) == "검토 의견"
    assert tables[0]["caption"] is None
    assert tables[1]["caption"] == "대안 비교표"


def test_diagram_spec():
    blocks = parse.parse_doc(DOC, is_text=True)["blocks"]
    dia = next(b for b in blocks if b["type"] == "diagram")
    assert dia["spec"]["type"] == "architecture"
    assert dia["spec"]["nodes"][0]["id"] == "api"


def test_image():
    blocks = parse.parse_doc(DOC, is_text=True)["blocks"]
    img = next(b for b in blocks if b["type"] == "image")
    assert img["path"] == "images/x.png" and img["caption"] == "구성도 설명"


DECK = """---
title: 덱 테스트
footer: 데이타솔루션
---
# 배경
<!-- layout: message -->
## 키가 흩어져 비용을 통제하지 못한다
- 키 개별 발급
- 로그 미보관
<!-- note: 발표자 노트 -->

---
# 목표 아키텍처
## 게이트웨이 한 곳에서 처리한다
```diagram
type: architecture
nodes:
  - { id: gw, label: Gateway }
```

---
# 대안 비교
## LiteLLM 이 기능이 가장 넓다
| 항목 | LiteLLM | 검토 의견 |
|---|---|---|
| 폴백 | 있음 | 적합 |
"""


def test_deck_slides():
    deck = parse.parse_deck(DECK, is_text=True)
    slides = deck["slides"]
    assert len(slides) == 3
    assert slides[0]["title"] == "배경"
    assert slides[0]["headline"].startswith("키가 흩어져")
    assert slides[0]["layout"] == "message"
    assert slides[0]["note"] == "발표자 노트"


def test_deck_layout_inference():
    slides = parse.parse_deck(DECK, is_text=True)["slides"]
    assert slides[1]["layout"] == "diagram"  # diagram 블록으로 추론
    assert slides[2]["layout"] == "table"  # 표로 추론
