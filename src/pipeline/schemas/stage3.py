from __future__ import annotations

from pydantic import BaseModel, field_validator

ARCHETYPES: list[str] = [
    "mechanical_system",
    "fluid_control",
    "thermal_exchange",
    "structural_support",
    "electrical_interface",
    "safety_relief",
    "measurement_control",
    "consumable_wear",
]


class AssemblyRecord(BaseModel):
    assembly_name: str
    archetype: str
    source: str
    description: str
    sub_assemblies: list[str] = []

    @field_validator("archetype")
    @classmethod
    def valid_archetype(cls, v: str) -> str:
        if v not in ARCHETYPES:
            raise ValueError(f"archetype must be one of {ARCHETYPES}")
        return v


class PartRecord(BaseModel):
    assembly_id: str
    part_name: str
    oem_part_number: str = "UNVERIFIED"
    brand: str = "UNVERIFIED"
    description: str
    quantity: int = 1
    unit: str = "ea"
    source_url: str = "UNVERIFIED"

    @field_validator("oem_part_number", "brand", "source_url")
    @classmethod
    def no_blank_unverified(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError("use 'UNVERIFIED' if unknown — never blank")
        return v
