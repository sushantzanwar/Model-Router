"""
features.py - Text -> model inputs
-----------------------------------
Two kinds of input, neither of which relies on a vocabulary or keyword list:

1. Hashed subword n-grams (fastText style). Every word, word bigram, character
   3-5 gram and symbol is hashed into a fixed number of buckets. The network learns
   what each bucket means from training examples; nothing is hand-mapped.
   Two bags are produced: the *instruction head* (what the user asks for) and the
   *full text* (which may include a long pasted payload).

2. Structural signals: language-agnostic statistics of the text's shape
   (symbol densities, line layout, numeric notation, script mix, payload ratio ...).
"""

import math
import re
import unicodedata
import zlib
from typing import List, Tuple

import numpy as np

NUM_BUCKETS = 1 << 16
HEAD_WORDS = 40
MAX_IDS = 1500

_WORD_RE = re.compile(r"\w+", re.UNICODE)
_SENT_RE = re.compile(r"[.!?。！？]+")
_ARITH_RE = re.compile(r"\d\s*[-+*/^=<>%]\s*\(?\s*[\d\w]")
_IDENT_RE = re.compile(r"[a-z][A-Z]|[A-Za-z0-9]_[A-Za-z0-9]|\w\.\w+\(")
_LIST_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
_URL_RE = re.compile(r"https?://|www\.")


def _h(token: str) -> int:
    return zlib.crc32(token.encode("utf-8")) % NUM_BUCKETS


def _split_instruction(text: str) -> Tuple[str, str]:
    """
    Separate the instruction (what is asked) from an attached payload (text to act on).
    Purely positional: first line if a block follows, else the first HEAD_WORDS words.
    """
    stripped = text.strip()
    if "\n" in stripped:
        first, rest = stripped.split("\n", 1)
        if len(first.split()) >= 2 and len(rest.strip()) > 0:
            return first, rest
    words = stripped.split()
    return " ".join(words[:HEAD_WORDS]), " ".join(words[HEAD_WORDS:])


def hashed_ids(text: str, limit: int = MAX_IDS) -> np.ndarray:
    lowered = text.lower()
    words = _WORD_RE.findall(lowered)
    ids: List[int] = []
    for i, w in enumerate(words):
        ids.append(_h("w|" + w))
        if i > 0:
            ids.append(_h("b|" + words[i - 1] + " " + w))
        padded = "<" + w + ">"
        if len(w) <= 24:
            for n in (3, 4, 5):
                for j in range(0, max(0, len(padded) - n + 1)):
                    ids.append(_h("c|" + padded[j:j + n]))
        if len(ids) >= limit:
            break
    for ch in set(lowered):
        if not ch.isalnum() and not ch.isspace():
            ids.append(_h("s|" + ch))
    if not ids:
        ids.append(_h("w|<empty>"))
    return np.asarray(ids[:limit + 64], dtype=np.int64)


def _script_of(ch: str) -> str:
    try:
        return unicodedata.name(ch).split(" ")[0]
    except ValueError:
        return "UNKNOWN"


STRUCT_NAMES = [
    "log_chars", "log_words", "log_sentences", "mean_sentence_len", "log_questions",
    "log_lines", "indent_ratio", "code_symbol_density", "code_fence", "operator_density",
    "digit_ratio", "log_arithmetic_patterns", "backslash_ratio", "non_ascii_letter_ratio",
    "script_count", "upper_ratio", "type_token_ratio", "avg_word_len", "long_word_ratio",
    "list_line_ratio", "payload_ratio", "log_head_words", "identifier_ratio",
    "comma_density", "quote_ratio", "has_url",
]

STRUCT_LABELS = {
    "log_chars": "prompt length",
    "log_words": "word count",
    "log_sentences": "number of sentences",
    "mean_sentence_len": "sentence length (clause depth)",
    "log_questions": "number of questions asked",
    "log_lines": "multi-line layout",
    "indent_ratio": "indented block structure",
    "code_symbol_density": "code-symbol density",
    "code_fence": "fenced code block",
    "operator_density": "operator density",
    "digit_ratio": "numeric content",
    "log_arithmetic_patterns": "arithmetic / equation notation",
    "backslash_ratio": "LaTeX / escape notation",
    "non_ascii_letter_ratio": "non-Latin characters",
    "script_count": "multiple writing systems",
    "upper_ratio": "capitalisation",
    "type_token_ratio": "lexical diversity",
    "avg_word_len": "average word length",
    "long_word_ratio": "technical (long) vocabulary",
    "list_line_ratio": "enumerated / list structure",
    "payload_ratio": "attached payload vs instruction",
    "log_head_words": "instruction length",
    "identifier_ratio": "programming identifiers",
    "comma_density": "clause density",
    "quote_ratio": "quoted material",
    "has_url": "URL reference",
}


def structural_features(text: str) -> np.ndarray:
    t = text.strip()
    n_chars = max(1, len(t))
    words = _WORD_RE.findall(t)
    n_words = max(1, len(words))
    sentences = [s for s in _SENT_RE.split(t) if s.strip()]
    n_sent = max(1, len(sentences))
    lines = [ln for ln in t.split("\n") if ln.strip()]
    n_lines = max(1, len(lines))

    code_syms = sum(t.count(c) for c in "{}[]();=<>_#$&|")
    ops = sum(t.count(c) for c in "+-*/^=%")
    digits = sum(ch.isdigit() for ch in t)
    letters = [ch for ch in t if ch.isalpha()]
    n_letters = max(1, len(letters))
    non_ascii = sum(1 for ch in letters if ord(ch) > 127)
    scripts = {_script_of(ch) for ch in letters[:400]}
    upper = sum(1 for ch in letters if ch.isupper())
    lowered_words = [w.lower() for w in words]
    head, payload = _split_instruction(t)

    feats = [
        math.log1p(n_chars),
        math.log1p(n_words),
        math.log1p(n_sent),
        min(4.0, (n_words / n_sent) / 15.0),
        math.log1p(t.count("?") + t.count("？")),
        math.log1p(n_lines - 1),
        sum(1 for ln in lines if ln.startswith(("  ", "\t"))) / n_lines,
        min(1.0, code_syms / n_chars * 8.0),
        1.0 if "```" in t else 0.0,
        min(1.0, ops / n_chars * 10.0),
        min(1.0, digits / n_chars * 5.0),
        math.log1p(len(_ARITH_RE.findall(t))),
        min(1.0, t.count("\\") / n_chars * 20.0),
        non_ascii / n_letters,
        float(max(0, len(scripts) - 1)),
        upper / n_letters,
        len(set(lowered_words)) / n_words,
        min(3.0, sum(len(w) for w in words) / n_words / 5.0),
        sum(1 for w in words if len(w) >= 9) / n_words,
        sum(1 for ln in lines if _LIST_RE.match(ln)) / n_lines,
        len(payload) / n_chars,
        math.log1p(len(head.split())),
        min(1.0, len(_IDENT_RE.findall(t)) / n_words * 4.0),
        min(2.0, (t.count(",") + t.count(";")) / n_words * 5.0),
        min(1.0, sum(t.count(c) for c in "\"'`“”") / n_chars * 20.0),
        1.0 if _URL_RE.search(t) else 0.0,
    ]
    return np.asarray(feats, dtype=np.float32)


def encode(text: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (instruction ids, full-text ids, structural vector)."""
    head, _ = _split_instruction(text)
    return hashed_ids(head, limit=400), hashed_ids(text), structural_features(text)
