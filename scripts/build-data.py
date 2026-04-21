#!/usr/bin/env python3
"""
build-data.py - Compile data/states.json from authoritative sources.

Sources:
  - US voter turnout:   UF Election Lab CSV            (fetched live)
  - US uninsured rate:  U.S. Census Bureau ACS API     (fetched live)
  - US life expectancy: CDC NVSR 74-12, Table A        (PDF; hand-extracted
                                                        TSV in data/raw/)

Running this script is idempotent: given the same upstream data and the same
committed TSV, it produces identical output. NYC and stories JSON are hand-
curated and are not touched.

Usage:
    python3 scripts/build-data.py

No third-party dependencies (stdlib only). Uses the public Census API, which
does not require a key for small queries.
"""
import csv
import io
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

UF_CSV_URL = (
    "https://election.lab.ufl.edu/data-downloads/turnoutdata/"
    "Turnout_2020G_v1.2.csv"
)
# S2701_C05_001E = Percent Uninsured; Estimate; civilian noninstitutionalized pop.
CENSUS_API_URL = (
    "https://api.census.gov/data/2023/acs/acs1/subject"
    "?get=NAME,S2701_C05_001E&for=state:*"
)
CDC_TSV = RAW_DIR / "cdc_nvsr_74_12_tableA.tsv"

# Display name overrides (e.g. shorter label for DC)
DISPLAY_NAME = {"DC": "Washington D.C."}

# Full name -> postal abbreviation. Used to join Census API responses (which
# return full names) with the rest of the dataset (keyed by abbr).
NAME_TO_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN",
    "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

# Turnout bucketing thresholds, mirroring tColor() in index.html.
HIGH_THRESHOLD = 70.0
MID_THRESHOLD = 64.0


def fetch_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "civic-health-ballot/build"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_uf_turnout() -> dict[str, float]:
    print(f"  GET {UF_CSV_URL}")
    text = fetch_url(UF_CSV_URL).decode("utf-8-sig")
    out: dict[str, float] = {}
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        name = row["STATE"].rstrip("*").strip()
        abbr = row["STATE_ABV"].strip()
        rate = row["VEP_TURNOUT_RATE"].rstrip("%").strip()
        if not abbr or name in ("United States",):
            continue
        if abbr == "US":
            continue
        out[abbr] = round(float(rate), 1)
    return out


def fetch_census_uninsured() -> dict[str, float]:
    print(f"  GET {CENSUS_API_URL}")
    payload = json.loads(fetch_url(CENSUS_API_URL).decode("utf-8"))
    headers, rows = payload[0], payload[1:]
    name_i = headers.index("NAME")
    pct_i = headers.index("S2701_C05_001E")
    out: dict[str, float] = {}
    for row in rows:
        name = row[name_i]
        if name == "Puerto Rico":
            continue
        abbr = NAME_TO_ABBR.get(name)
        if not abbr:
            print(f"  WARN: no abbr mapping for {name!r}", file=sys.stderr)
            continue
        out[abbr] = round(float(row[pct_i]), 1)
    return out


def load_cdc_life_expectancy() -> dict[str, float]:
    print(f"  READ {CDC_TSV.relative_to(ROOT)}")
    out: dict[str, float] = {}
    with CDC_TSV.open() as f:
        # Skip comment lines (starting with #)
        lines = [ln for ln in f if not ln.startswith("#")]
    reader = csv.DictReader(lines, delimiter="\t")
    for row in reader:
        abbr = row["abbr"].strip()
        out[abbr] = round(float(row["le_2022"]), 1)
    return out


def build_groups(states: dict[str, dict]) -> dict[str, list[str]]:
    """Bucket state codes by turnout, sorted within each bucket descending."""
    items = sorted(states.items(), key=lambda kv: -kv[1]["t"])
    high, mid, low = [], [], []
    for abbr, s in items:
        t = s["t"]
        if t >= HIGH_THRESHOLD:
            high.append(abbr)
        elif t >= MID_THRESHOLD:
            mid.append(abbr)
        else:
            low.append(abbr)
    return {"high": high, "mid": mid, "low": low}


def main() -> int:
    print("Fetching US turnout (UF Election Lab)...")
    turnout = fetch_uf_turnout()
    print(f"  {len(turnout)} entries")

    print("Fetching US uninsured rate (Census ACS 1-year 2023)...")
    uninsured = fetch_census_uninsured()
    print(f"  {len(uninsured)} entries")

    print("Loading US life expectancy (CDC NVSR 74-12, Table A)...")
    life = load_cdc_life_expectancy()
    print(f"  {len(life)} entries")

    all_abbrs = sorted(set(turnout) | set(uninsured) | set(life))
    abbr_to_name = {v: k for k, v in NAME_TO_ABBR.items()}

    states: dict[str, dict] = {}
    for abbr in all_abbrs:
        missing = [k for k, src in
                   (("t", turnout), ("u", uninsured), ("l", life))
                   if abbr not in src]
        if missing:
            print(f"  SKIP {abbr}: missing {missing}", file=sys.stderr)
            continue
        entry = {
            "name": DISPLAY_NAME.get(abbr) or abbr_to_name[abbr],
            "t": turnout[abbr],
            "u": uninsured[abbr],
            "l": life[abbr],
        }
        if abbr == "NY":
            entry["special"] = True
        states[abbr] = entry

    print(f"Merged dataset: {len(states)} states + DC")

    groups = build_groups(states)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    states_doc = {
        "_generated_at": now,
        "_thresholds": {
            "high": HIGH_THRESHOLD,
            "mid": MID_THRESHOLD,
        },
        "states": states,
        "groups": groups,
    }

    sources_doc = {
        "_generated_at": now,
        "us_turnout": {
            "metric_key": "t",
            "description": "2020 general election voter turnout, voting-eligible population.",
            "publisher": "UF Election Lab",
            "dataset": "Turnout_2020G v1.2",
            "landing_url": "https://election.lab.ufl.edu/voter-turnout/2020-general-election-turnout/",
            "fetch_url": UF_CSV_URL,
            "fetched_at": now,
        },
        "us_uninsured": {
            "metric_key": "u",
            "description": "Percent uninsured, civilian noninstitutionalized population, 2023.",
            "publisher": "U.S. Census Bureau, American Community Survey (ACS) 1-year",
            "dataset": "S2701 (2023), variable S2701_C05_001E",
            "landing_url": "https://data.census.gov/table/ACSST1Y2023.S2701",
            "fetch_url": CENSUS_API_URL,
            "fetched_at": now,
            "mirror": "https://www.kff.org/state-category/health-coverage-uninsured/",
        },
        "us_life_expectancy": {
            "metric_key": "l",
            "description": "Life expectancy at birth, 2022.",
            "publisher": "CDC/NCHS, National Vital Statistics System",
            "dataset": (
                "National Vital Statistics Reports Vol. 74 No. 12 "
                "(U.S. State Life Tables, 2022), Table A"
            ),
            "landing_url": "https://www.cdc.gov/nchs/data/nvsr/nvsr74/nvsr74-12.pdf",
            "local_extract": str(CDC_TSV.relative_to(ROOT)),
            "note": (
                "CDC publishes NVSR only as PDF. The local TSV is the canonical "
                "input; re-extract and commit when a newer NVSR is released."
            ),
        },
    }

    (DATA_DIR / "states.json").write_text(
        json.dumps(states_doc, indent=2) + "\n"
    )
    (DATA_DIR / "sources.json").write_text(
        json.dumps(sources_doc, indent=2) + "\n"
    )
    print(f"Wrote {DATA_DIR / 'states.json'}")
    print(f"Wrote {DATA_DIR / 'sources.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
