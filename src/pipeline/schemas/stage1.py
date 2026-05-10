from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, field_validator


class OrgRecord(BaseModel):
    name: str
    source_url: str
    category: int
    employee_count: Optional[int] = None
    pe_backed: bool = False
    pe_owner: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("source_url")
    @classmethod
    def source_url_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_url must not be empty — use 'UNVERIFIED' if unknown")
        return v


class PlayerMap(BaseModel):
    industry: str
    region: str
    categories: dict[int, list[OrgRecord]] = {}
    completed_categories: list[int] = []
    flags: list[str] = []

    def add(self, category: int, orgs: list[OrgRecord]) -> None:
        self.categories[category] = orgs

    def mark_complete(self, category: int) -> None:
        if category not in self.completed_categories:
            self.completed_categories.append(category)

    def flag(self, message: str) -> None:
        self.flags.append(message)
