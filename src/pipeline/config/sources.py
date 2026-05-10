from dataclasses import dataclass, field


@dataclass
class SourceConfig:
    name: str
    base_url: str
    query_template: str  # supports {industry}, {region}, {adjacent_trade} placeholders
    fields: list[str] = field(default_factory=list)


SOURCE_REGISTRY: dict[int, list[SourceConfig]] = {
    1: [  # Industry associations & regulatory bodies
        SourceConfig(
            name="provincial_regulator",
            base_url="https://www.rbq.gouv.qc.ca",
            query_template="{industry} contractors licence members {region}",
            fields=["name", "licence_number", "address", "source_url"],
        ),
        SourceConfig(
            name="trade_association_directory",
            base_url="https://www.google.com/search",
            query_template='"{industry}" association members directory {region}',
            fields=["name", "source_url", "description"],
        ),
    ],
    2: [  # National distributors
        SourceConfig(
            name="google_national_distributors",
            base_url="https://www.google.com/search",
            query_template='"{industry}" national distributor Canada revenue employees',
            fields=["name", "source_url", "employee_count", "revenue"],
        ),
        SourceConfig(
            name="ibisworld",
            base_url="https://www.ibisworld.com",
            query_template="{industry} distribution companies Canada market share",
            fields=["name", "revenue", "employee_count", "source_url"],
        ),
    ],
    3: [  # Regional distributors
        SourceConfig(
            name="google_regional_distributors",
            base_url="https://www.google.com/search",
            query_template='"{industry}" distributor {region}',
            fields=["name", "source_url", "address"],
        ),
        SourceConfig(
            name="yellowpages",
            base_url="https://www.yellowpages.ca",
            query_template="{industry} wholesale distributor {region}",
            fields=["name", "source_url", "phone", "address"],
        ),
    ],
    4: [  # Manufacturers / OEMs
        SourceConfig(
            name="google_manufacturers",
            base_url="https://www.google.com/search",
            query_template='"{industry}" manufacturer OEM Canada {region}',
            fields=["name", "source_url", "product_lines", "employee_count"],
        ),
        SourceConfig(
            name="thomasnet",
            base_url="https://www.thomasnet.com",
            query_template="{industry} parts manufacturer {region}",
            fields=["name", "source_url", "certifications", "employee_count"],
        ),
    ],
    5: [  # Contractors — minimum 15 required
        SourceConfig(
            name="google_maps_contractors",
            base_url="https://www.google.com/maps",
            query_template="{industry} contractor {region}",
            fields=["name", "source_url", "rating", "reviews_count"],
        ),
        SourceConfig(
            name="bbb_contractors",
            base_url="https://www.bbb.org",
            query_template="{industry} contractor {region}",
            fields=["name", "source_url", "accredited", "rating"],
        ),
        SourceConfig(
            name="yelp_contractors",
            base_url="https://www.yelp.ca",
            query_template="{industry} contractor {region}",
            fields=["name", "source_url", "rating", "reviews_count"],
        ),
    ],
    6: [  # Maintenance & service companies
        SourceConfig(
            name="google_service_companies",
            base_url="https://www.google.com/search",
            query_template='"{industry}" maintenance service company {region}',
            fields=["name", "source_url", "employee_count"],
        ),
        SourceConfig(
            name="yellowpages_service",
            base_url="https://www.yellowpages.ca",
            query_template="{industry} maintenance service {region}",
            fields=["name", "source_url", "phone", "address"],
        ),
    ],
    7: [  # Wholesalers
        SourceConfig(
            name="google_wholesalers",
            base_url="https://www.google.com/search",
            query_template='"{industry}" wholesale supplier {region}',
            fields=["name", "source_url", "employee_count"],
        ),
        SourceConfig(
            name="canadian_business_directory",
            base_url="https://www.canadianbusiness.com",
            query_template="{industry} wholesale {region}",
            fields=["name", "source_url", "revenue"],
        ),
    ],
    8: [  # Adjacent trades
        SourceConfig(
            name="google_adjacent_trades",
            base_url="https://www.google.com/search",
            query_template='"{adjacent_trade}" contractor distributor manufacturer {region}',
            fields=["name", "source_url", "description"],
        ),
    ],
}

CATEGORY_NAMES: dict[int, str] = {
    1: "Industry Associations & Regulatory Bodies",
    2: "National Distributors",
    3: "Regional Distributors",
    4: "Manufacturers / OEMs",
    5: "Contractors",
    6: "Maintenance & Service Companies",
    7: "Wholesalers",
    8: "Adjacent Trades",
}

ADJACENT_TRADES: dict[str, list[str]] = {
    "plumbing": ["HVAC", "fire protection", "gas fitting", "waterproofing"],
    "hvac": ["plumbing", "electrical", "refrigeration", "building automation"],
    "electrical": ["data/telecom", "fire alarm", "HVAC controls", "solar"],
    "mechanical": ["plumbing", "HVAC", "fire protection", "electrical"],
}
