from __future__ import annotations

from pydantic import BaseModel, field_validator


class BuyerProfile(BaseModel):
    player_type: str
    pain_points: list[str]
    leverage_points: list[str]
    top_3_influencers: list[str]
    sources_consulted: list[str] = []

    @field_validator("pain_points", "leverage_points")
    @classmethod
    def non_empty_list(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("list must not be empty")
        return v

    @field_validator("top_3_influencers")
    @classmethod
    def exactly_three(cls, v: list[str]) -> list[str]:
        if len(v) != 3:
            raise ValueError("top_3_influencers must contain exactly 3 entries")
        return v


class FrictionMap(BaseModel):
    industry: str
    region: str
    profiles: dict[str, BuyerProfile] = {}

    def add(self, profile: BuyerProfile) -> None:
        self.profiles[profile.player_type] = profile
