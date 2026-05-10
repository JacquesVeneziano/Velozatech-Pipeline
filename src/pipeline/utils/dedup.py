from __future__ import annotations

import re
from urllib.parse import urlparse

from pipeline.schemas.stage1 import OrgRecord

_LEGAL_SUFFIXES = re.compile(
    r"\b(inc|ltée|ltee|corp|ltd|llc|group|groupe|inc\.|ltée\.|corp\.|ltd\.)\b",
    re.IGNORECASE,
)

MERGE_THRESHOLD = 0.8
AMBIGUOUS_LOW = 0.5
AMBIGUOUS_HIGH = 0.8


def normalise_name(name: str) -> set[str]:
    name = _LEGAL_SUFFIXES.sub("", name.lower())
    name = re.sub(r"[^\w\s]", "", name)
    return set(name.split())


def token_overlap(a: str, b: str) -> float:
    tokens_a = normalise_name(a)
    tokens_b = normalise_name(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def domain_root(url: str) -> str:
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        host = (parsed.netloc or parsed.path).lstrip("www.")
        parts = host.split(".")
        return ".".join(parts[-2:]) if len(parts) >= 2 else host
    except Exception:
        return url


def should_merge(a: OrgRecord, b: OrgRecord) -> bool:
    score = token_overlap(a.name, b.name)
    if score >= MERGE_THRESHOLD:
        return True
    if AMBIGUOUS_LOW <= score < AMBIGUOUS_HIGH:
        return domain_root(a.source_url) == domain_root(b.source_url)
    return False


def merge_records(existing: OrgRecord, incoming: OrgRecord) -> OrgRecord:
    """Keeps existing record; enriches any None fields from incoming."""
    data = existing.model_dump()
    for key, value in incoming.model_dump().items():
        if data.get(key) is None and value is not None:
            data[key] = value
    return OrgRecord(**data)


def dedup_merge(existing: list[OrgRecord], incoming: list[OrgRecord]) -> list[OrgRecord]:
    result = list(existing)
    for candidate in incoming:
        merged = False
        for i, record in enumerate(result):
            if should_merge(record, candidate):
                result[i] = merge_records(record, candidate)
                merged = True
                break
        if not merged:
            result.append(candidate)
    return result
