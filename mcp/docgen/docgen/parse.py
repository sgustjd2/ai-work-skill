"""`.doc.md` / `.deck.md` 파서: frontmatter + 블록 모델. 렌더러 3종이 이 블록을 소비한다.

블록 타입: heading, paragraph, list, table, code, diagram, timeline, chart, image, blockquote,
pagebreak, hr, col. 인라인 run: text/code/image (bold·italic·strike·link 플래그).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from markdown_it import MarkdownIt

_MD = MarkdownIt("commonmark", {"html": True}).enable("table")
try:
    _MD.enable("strikethrough")
except Exception:  # 규칙 없으면 무시
    pass


# ─── 인라인 ──────────────────────────────────────────────────────────────────
def _runs(inline):
    out = []
    bold = italic = strike = 0
    link = None
    for t in (inline.children or []) if inline else []:
        if t.type == "text":
            if t.content:
                out.append(_run(t.content, bold, italic, strike, link))
        elif t.type == "code_inline":
            out.append({"kind": "code", "text": t.content})
        elif t.type == "strong_open":
            bold += 1
        elif t.type == "strong_close":
            bold = max(0, bold - 1)
        elif t.type == "em_open":
            italic += 1
        elif t.type == "em_close":
            italic = max(0, italic - 1)
        elif t.type == "s_open":
            strike += 1
        elif t.type == "s_close":
            strike = max(0, strike - 1)
        elif t.type == "link_open":
            link = dict(t.attrs).get("href")
        elif t.type == "link_close":
            link = None
        elif t.type in ("softbreak", "hardbreak"):
            out.append(_run(" ", bold, italic, strike, link))
        elif t.type == "image":
            out.append({"kind": "image", "path": dict(t.attrs).get("src", ""), "alt": t.content})
    return out


def _run(text, bold, italic, strike, link):
    return {
        "kind": "text",
        "text": text,
        "bold": bold > 0,
        "italic": italic > 0,
        "strike": strike > 0,
        "link": link,
    }


def runs_text(runs):
    return "".join(r.get("text", "") for r in runs)


# ─── 토큰 -> 블록 ────────────────────────────────────────────────────────────
def _find_close(tokens, i, open_t, close_t):
    depth = 1
    while i < len(tokens):
        if tokens[i].type == open_t:
            depth += 1
        elif tokens[i].type == close_t:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(tokens)


def _safe_yaml(text):
    try:
        v = yaml.safe_load(text)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _html_comment(content):
    m = re.search(r"<!--\s*(.*?)\s*-->", content, re.S)
    if not m:
        return None
    inner = m.group(1).strip()
    if inner == "pagebreak":
        return {"type": "pagebreak"}
    if inner == "col":
        return {"type": "col"}
    for prefix, typ in (
        ("caption:", "caption"),
        ("layout:", "layout"),
        ("note:", "note"),
        ("source:", "source"),
    ):
        if inner.lower().startswith(prefix):
            return {"type": typ, "text": inner[len(prefix) :].strip()}
    return None


def _parse_table(tokens, start):
    end = _find_close(tokens, start, "table_open", "table_close")
    inner = tokens[start:end]
    header, rows, align = [], [], []
    cur, in_head = [], False
    for t in inner:
        if t.type == "thead_open":
            in_head = True
        elif t.type == "thead_close":
            in_head = False
        elif t.type == "tr_open":
            cur = []
        elif t.type == "tr_close":
            if in_head:
                header = cur
            else:
                rows.append(cur)
        elif t.type in ("th_open", "td_open"):
            if t.type == "th_open":
                st = dict(t.attrs).get("style", "")
                align.append("right" if "right" in st else "center" if "center" in st else "left")
            cur.append([])
        elif t.type == "inline":
            cur[-1] = _runs(t)
    tbl = {"type": "table", "header": header, "rows": rows, "align": align, "caption": None}
    return tbl, end + 1


def _parse_list(tokens, start, open_t, close_t):
    end = _find_close(tokens, start, open_t, close_t)
    inner = tokens[start:end]
    items = []
    j = 0
    while j < len(inner):
        if inner[j].type == "list_item_open":
            ie = _find_close(inner, j + 1, "list_item_open", "list_item_close")
            items.append(_parse_tokens(inner[j + 1 : ie]))
            j = ie + 1
        else:
            j += 1
    return items, end + 1


def _parse_tokens(tokens):
    blocks = []
    pending_caption = None
    i = 0
    while i < len(tokens):
        t = tokens[i]
        tt = t.type
        if tt == "heading_open":
            runs = _runs(tokens[i + 1])
            blocks.append(
                {"type": "heading", "level": int(t.tag[1:]), "text": runs_text(runs), "runs": runs}
            )
            i += 3
        elif tt == "paragraph_open":
            runs = _runs(tokens[i + 1])
            imgs = [r for r in runs if r["kind"] == "image"]
            texty = [r for r in runs if r["kind"] != "image" and r.get("text", "").strip()]
            if imgs and not texty:
                blocks.append(
                    {"type": "image", "path": imgs[0]["path"], "caption": imgs[0].get("alt", "")}
                )
            else:
                blocks.append({"type": "paragraph", "runs": runs})
            i += 3
        elif tt == "fence":
            info = (t.info or "").strip().split(" ")[0] if (t.info or "").strip() else ""
            if info in ("diagram", "timeline", "chart"):
                blocks.append({"type": info, "spec": _safe_yaml(t.content), "raw": t.content})
            else:
                blocks.append({"type": "code", "lang": info, "content": t.content})
            i += 1
        elif tt == "code_block":
            blocks.append({"type": "code", "lang": "", "content": t.content})
            i += 1
        elif tt == "hr":
            blocks.append({"type": "hr"})
            i += 1
        elif tt == "html_block":
            b = _html_comment(t.content)
            if b and b["type"] == "caption":
                pending_caption = b["text"]
            elif b:
                blocks.append(b)
            i += 1
        elif tt in ("bullet_list_open", "ordered_list_open"):
            close = "bullet_list_close" if tt == "bullet_list_open" else "ordered_list_close"
            items, i = _parse_list(tokens, i + 1, tt, close)
            blocks.append({"type": "list", "ordered": tt == "ordered_list_open", "items": items})
        elif tt == "blockquote_open":
            end = _find_close(tokens, i + 1, "blockquote_open", "blockquote_close")
            blocks.append({"type": "blockquote", "blocks": _parse_tokens(tokens[i + 1 : end])})
            i = end + 1
        elif tt == "table_open":
            tbl, i = _parse_table(tokens, i + 1)
            tbl["caption"] = pending_caption
            pending_caption = None
            blocks.append(tbl)
        else:
            i += 1
    return blocks


# ─── 공개 API ────────────────────────────────────────────────────────────────
def _split_frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        fm = {}
    return (fm if isinstance(fm, dict) else {}), text[m.end() :]


def _read(source, is_text):
    return source if is_text else Path(source).read_text(encoding="utf-8")


def parse_doc(source, is_text=False):
    fm, body = _split_frontmatter(_read(source, is_text))
    blocks = [b for b in _parse_tokens(_MD.parse(body)) if b["type"] != "hr"]
    return {"frontmatter": fm, "blocks": blocks}


def _infer_layout(blocks):
    types = {b["type"] for b in blocks}
    for kind in ("diagram", "timeline", "chart", "table"):
        if kind in types:
            return kind
    if "col" in types:
        return "two-col"
    if "image" in types:
        return "image"
    return "message"


def parse_deck(source, is_text=False):
    fm, body = _split_frontmatter(_read(source, is_text))
    blocks = _parse_tokens(_MD.parse(body))
    groups, cur = [], []
    for b in blocks:
        if b["type"] == "hr":
            groups.append(cur)
            cur = []
        else:
            cur.append(b)
    groups.append(cur)

    slides = []
    for sb in [g for g in groups if g]:
        s = {
            "title": None,
            "headline": None,
            "layout": None,
            "note": None,
            "source": None,
            "blocks": [],
        }
        for b in sb:
            if b["type"] == "heading" and b["level"] == 1 and s["title"] is None:
                s["title"] = b["text"]
            elif b["type"] == "heading" and b["level"] == 2 and s["headline"] is None:
                s["headline"] = b["text"]
            elif b["type"] in ("layout", "note", "source"):
                s[b["type"]] = b["text"]
            else:
                s["blocks"].append(b)
        s["layout"] = s["layout"] or _infer_layout(s["blocks"])
        slides.append(s)
    return {"frontmatter": fm, "slides": slides}
