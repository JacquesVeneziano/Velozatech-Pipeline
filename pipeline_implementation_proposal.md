# 🏗️ Part Opportunity Vetting Pipeline — Implementation Proposal

*Technical architecture for operationalising the 3-stage intelligence pipeline as production-grade Python code.*

---

## 🧭 The Core Architectural Tension

The pipeline mixes two fundamentally different kinds of work that must be separated cleanly.

**🧠 Intelligence work** — things only a language model can do well: formulating the right query for a specific source, extracting structured data from unstructured HTML, determining whether "Groupe Master" and "Master Distribution Inc." are the same entity, synthesising pain points from forum posts, assessing whether an org is likely PE-backed based on vague signals.

**⚙️ Deterministic work** — things that must never be delegated to an LLM: enforcing a minimum of 15 contractors before closing a category, checking that every org object has a `source_url` field, comparing a publication date against a 24-month threshold, running a PE check for every org with 50+ employees.

The risk of leaving all logic inside a skill file is that Claude can drift — convincing itself a category is done when it isn't, skipping the dominant player validation step under cognitive load, or forgetting adjacent trade searches when context grows long. **The deterministic logic must live in code, not in a prompt.**

---

## 🐍 Language & Stack

**Python** is the right choice throughout, for three reasons:

1. `openpyxl` is already the established Excel tool in this project and `build_export.py` already exists in the Stage 3 skill — no reinvention needed.
2. **Pydantic** is a natural fit for the strict output schemas defined in the skills — every `org`, `buyer_profile`, and `part` record becomes a validated model that refuses to be created if required fields are missing or mistyped.
3. Python's async support makes parallelising web searches within a category straightforward.

For web research, **WebSearch** and **WebFetch** are the execution tools. The implementation wraps these in thin Python functions that return structured results and automatically flag staleness based on extracted publication dates.

---

## 🗂️ Project Organisation

```
pipeline/
│
├── run.py                          # 🚀 CLI entry point
│                                   #    run_pipeline --stage 1 --industry "Plumbing" --region "Montreal"
│
├── config/
│   ├── sources.py                  # 📚 Source registry — maps each category to allowed
│   │                               #    sources in priority order (enforces source lock)
│   ├── minimums.py                 # 🔢 Minimum count constants per Stage 1 category
│   └── pe_firms.py                 # 🏦 Quebec PE firm portfolio URLs
│                                   #    (Novacap, FTQ, Investissement Québec, Caisse de dépôt)
│
├── schemas/
│   ├── stage1.py                   # 🏢 Pydantic: OrgRecord, PlayerMap
│   ├── stage2.py                   # 🛒 Pydantic: BuyerProfile, FrictionMap
│   └── stage3.py                   # 🔩 Pydantic: AssemblyRecord (Phase A), PartRecord (Phase B)
│
├── stages/
│   ├── stage1/
│   │   ├── runner.py               # 🎯 Orchestrates categories 1–8 in order
│   │   ├── categories.py           # 🔍 One function per category — search logic + source progression
│   │   ├── validation.py           # ✅ Dominant player validation, PE check, adjacent trade search
│   │   └── output.py              # 📋 Formats and writes stage1_output.json + required footer
│   │
│   ├── stage2/
│   │   ├── runner.py               # 🎯 Orchestrates player type analysis
│   │   ├── sources.py              # 🔎 14 source handlers — one per source type
│   │   └── synthesis.py            # 🧩 Aggregates raw signals into buyer profile per player type
│   │
│   └── stage3/
│       ├── phase_a.py              # 🗺️ Taxonomy mapping — 7 sources × 8 archetypes
│       ├── phase_b.py              # 🔬 Assembly decomposition — drill-down logic
│       ├── phase_c.py              # 📊 Invokes build_export.py with Phase B data
│       └── scripts/
│           └── build_export.py     # 📁 Already exists — copied from Stage 3 skill
│
├── state/                          # 💾 Persisted inter-stage state (enables resume)
│   ├── stage1_output.json
│   ├── stage2_output.json
│   ├── stage3_taxonomy.json
│   └── stage3_drilldown/
│       └── [assembly_id].json      # One file per assembly drill-down
│
└── utils/
    ├── search.py                   # 🌐 WebSearch + WebFetch wrappers with staleness detection
    ├── dedup.py                    # 🔄 Fuzzy org name matching
    └── citations.py                # 📎 Citation validation — enforces source_url or flags UNVERIFIED
```

---

## ⚙️ Stage 1 — Player Mapping Implementation

Stage 1 is the most complex to implement correctly because of its nested validation logic.

### 🔁 Runner Loop

```python
for category in CATEGORIES:                          # 1 through 8, in order
    results = []
    for source in SOURCE_REGISTRY[category]:         # Try sources in priority order
        new_results = search_source(source, query)
        results = dedup_merge(results, new_results)  # Fuzzy match before adding
        if len(results) >= MINIMUMS[category]:
            break

    if len(results) < MINIMUMS[category]:
        flag_below_minimum(category, len(results))   # Flag but don't abort

    # Dominant player validation — always runs, non-skippable
    validation_results = run_dominant_player_validation(category, industry, region)
    results = merge_missing(results, validation_results)

    # PE check — runs inline for Categories 2, 3, 4
    if category in [2, 3, 4]:
        for org in results:
            if org.employee_count >= 50:
                org.pe_backed, org.pe_owner = run_pe_check(org.name, region)

    persist_category(category, results)              # 💾 Save to JSON after each category
    player_map.add(category, results)
```

### 📚 Source Registry (`config/sources.py`)

The source registry encodes the **source lock** — each category maps to an ordered list of sources, and the search loop is only allowed to query from that list. This prevents the model from going off-script. Each source object includes:

- Base URL
- Query template (parameterised by industry, region, adjacent trade)
- List of fields to extract from results

### 🔄 Deduplication (`utils/dedup.py`)

The `dedup_merge` function is non-trivial. Org names in the wild vary: "Groupe Master", "Master Group", "Groupe Master Inc." are all the same company. Implementation uses **two-pass comparison**:

1. **Token overlap scoring** on normalised names (lowercase, strip legal suffixes: "Inc.", "Ltée", "Corp.", "Ltd.") with a threshold of 0.7.
2. If token overlap falls in the ambiguous 0.5–0.8 range: **compare the domain of `source_url`** as a tiebreaker. Two orgs pointing to the same domain root are almost certainly the same entity.

| Overlap Score | Domain match | Action |
|---|---|---|
| ≥ 0.8 | Any | Merge immediately |
| 0.5–0.8 | Same domain | Merge |
| 0.5–0.8 | Different domain | Treat as distinct |
| < 0.5 | Any | Treat as distinct |

### 💾 State Persistence

Stage 1 involves dozens of web searches and can run for 15–30 minutes on a real industry. If it fails mid-way through, the pipeline must resume from the last completed category rather than starting over. A `completed_categories` array in `state/stage1_output.json` is updated after each category passes validation. On resume, the runner skips any category already in that array.

---

## 🛒 Stage 2 — Buyer & Influencer Analysis Implementation

Stage 2 is more qualitative and source-driven. The 14 sources are fundamentally different in nature:

- **Structured data sources** (RFP portals, business registries) → parsed directly into fields
- **Unstructured text sources** (forums, YouTube, employer reviews) → LLM synthesis pass
- **UI-navigated sources** (distributor locator maps) → WebFetch with structured extraction

### 🔌 One Handler Per Source Type

Each of the 14 sources gets its own handler in `stages/stage2/sources.py`, keyed by source priority number. Each handler:
1. Constructs the source-specific query
2. Executes the fetch
3. Returns a list of raw signal strings

Then `synthesis.py` runs a **single LLM pass** over all signals for a given player type to produce the final `BuyerProfile` object. Pydantic enforces that `pain_points`, `leverage_points`, and `top_3_influencers` are non-empty lists before the profile is accepted.

### 💡 Sources 13 & 14 — The Underused Signal

Surplus dealers (Source 13) and secondary marketplaces (Source 14 — eBay, Kijiji, Facebook Marketplace) are particularly valuable. They are essentially a **real-time signal of what the normal supply chain has failed to provide** — what's listed at 3× MSRP on Kijiji is a direct answer to "what parts are buyers most desperate for."

Implementation extracts per listing: `part_name`, `brand`, `listed_price`, `seller_type` (individual vs. trade). The **delta between MSRP and secondary market price** becomes a proxy for supply gap severity — a key input for Stage 4 part prioritisation.

---

## 🔩 Stage 3 — Assembly Decomposition Implementation

### 🗺️ Phase A — Taxonomy (7 sources × 8 archetypes)

The 7 sources run in order, each mapping findings onto the 8 universal archetypes. Output accumulates across sources:

- Regulatory scope reading → likely finds archetypes 1, 2, 4, 8
- Distributor product tree → fills in archetypes 3, 5, 6, 7

**Source 3 (distributor product category tree) is the highest-signal source.** It reflects what the market actually buys, not what the regulator says should be maintained. Implementation uses `WebFetch` against each Stage 1 distributor's root URL and walks their category hierarchy recursively, with a depth limit of 3 to avoid infinite traversal.

The minimum count checker runs after all 7 sources complete and flags any archetype below minimum before presenting the taxonomy to the operator for confirmation. **Phase B cannot begin without operator confirmation.**

### 🔬 Phase B — Assembly Drill-Down (parallelisable)

Phase B is the most parallelisable part of the entire pipeline. Each assembly drill-down is independent once the taxonomy is confirmed. The **Agent tool** runs 4–6 assembly decompositions in parallel, each as a subagent with WebSearch + WebFetch access. Each subagent writes to a separate JSON file in `state/stage3_drilldown/` to avoid write conflicts.

**Critical rule enforced at schema level:** every part record must have `UNVERIFIED` (not `null`, not blank) in `oem_part_number` if the SKU wasn't confirmed. The Pydantic `PartRecord` schema enforces this at Phase B output time — not deferred to Phase C.

```python
class PartRecord(BaseModel):
    oem_part_number: str = "UNVERIFIED"  # Default forces explicit assignment

    @validator("oem_part_number")
    def no_blank_part_number(cls, v):
        if v.strip() == "":
            raise ValueError("oem_part_number must be 'UNVERIFIED' if unknown — never blank")
        return v
```

### 📊 Phase C — Excel Export

Phase C is almost purely mechanical. The `build_export.py` script already exists — the implementation loads completed Phase B JSON files for the requested assemblies and passes them as structured arguments. The Phase C runner in `phase_c.py`:

1. Reads `state/stage3_drilldown/[assembly_id].json` for each requested assembly
2. Deserialises into `list[PartRecord]` (validates completeness)
3. Calls `build_export.py` with the structured data
4. Outputs to `stage3-drill-down-[assembly-id]-[YYYY-MM-DD].xlsx`

---

## 🔑 Highest-Leverage Engineering Investment

The **fuzzy org deduplication** in Stage 1 is the single highest-leverage engineering investment. The dominant player validation, adjacent trade search, and PE check all depend on correctly identifying whether an org is already in the results list.

Get this wrong and the pipeline either creates duplicates (inflating counts and creating false confidence in category completion) or silently discards valid new entries found via validation queries. The two-pass algorithm described above is the minimum viable implementation — for production, adding a secondary check against registered business numbers (REQ in Quebec, federal CBCA) would make it nearly bulletproof.

---

## 🏗️ Build Order

The order of implementation matters. Build in this sequence:

| # | What | Why First |
|---|---|---|
| 1 | 📐 Pydantic schemas | Defines the contract everything else is built against |
| 2 | 🌐 `search.py` utility with staleness detection | Every stage depends on this — get it right once |
| 3 | ⚙️ Stage 1, Category 4 first (Distributors) | Most complex logic — adjacent trade, PE check, dominant player validation. If Cat 4 works, Cats 2, 3, 5–8 are mostly parameter changes |
| 4 | 📊 Stage 3 Phase C + Pydantic-to-dict serialisation | Gives a concrete deliverable to validate against early; forces Part schema to be complete before Phase B |
| 5 | 🔍 Stages 2 and 3 Phases A and B | Built with confidence that scaffolding is solid |

---

## 📐 Layer Summary

| Layer                | Tool / Library                               | Role                                             |
| -------------------- | -------------------------------------------- | ------------------------------------------------ |
| 🚀 Orchestration     | Python `run.py`                              | Stage sequencing, state loading, resume logic    |
| 📐 Schema validation | Pydantic                                     | Enforces output contracts for every stage        |
| 🌐 Web research      | WebSearch + WebFetch                         | Executes source-locked queries                   |
| 🧠 Intelligence      | Claude (via skills)                          | Query formulation, text extraction, synthesis    |
| 🔄 Deduplication     | Custom Python (token overlap + domain match) | Prevents duplicate orgs, catches name variants   |
| 💾 State persistence | JSON files in `state/`                       | Enables mid-stage resume, inter-stage handoff    |
| ⚡ Parallelisation    | Agent tool (Stage 3 Phase B)                 | Runs assembly drill-downs concurrently           |
| 📊 Excel export      | openpyxl (`build_export.py`)                 | Phase C — already written, just needs invocation |

---

## 🎯 Guiding Principle

> The pipeline as written in the skills is a research specification. The implementation job is to wrap that specification in just enough deterministic scaffolding that the validation logic is never at risk of being skipped — while keeping Claude in the loop for everything that genuinely requires judgment.

Every piece of logic that can be expressed as code should be expressed as code. Every piece of logic that requires reading an unstructured webpage, recognising a company across name variants, or synthesising friction from 40 Reddit posts — that stays with the model.
