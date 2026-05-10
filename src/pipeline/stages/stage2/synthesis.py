from __future__ import annotations

from pipeline.schemas.stage2 import BuyerProfile


def synthesise_buyer_profile(player_type: str, signals: list[str]) -> BuyerProfile:
    """
    Stub — Claude reads the signal strings and produces a structured BuyerProfile.
    The stub returns placeholders so the pipeline runs end-to-end in dry-run mode.
    Replace with an actual LLM synthesis call when wiring up the intelligence layer.
    """
    return BuyerProfile(
        player_type=player_type,
        pain_points=["[STUB] awaiting synthesis from signals"],
        leverage_points=["[STUB] awaiting synthesis from signals"],
        top_3_influencers=[
            "[STUB] influencer 1",
            "[STUB] influencer 2",
            "[STUB] influencer 3",
        ],
        sources_consulted=[],
    )
