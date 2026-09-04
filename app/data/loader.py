import csv
import glob
import random
import re
from pathlib import Path
from typing import List, Dict, Any, Generator
from app.config import DATA_DIR

STATE_ABBREV = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
    "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
    "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
    "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
    "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
    "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
    "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
    "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
    "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT",
    "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI", "WYOMING": "WY", "PUERTO RICO": "PR"
}


def normalize_state(state_str: str) -> str:
    """Normalize state string to 2-letter postal abbreviation."""
    if not state_str:
        return None
    cleaned = state_str.strip().upper()
    if len(cleaned) == 2:
        return cleaned
    return STATE_ABBREV.get(cleaned, cleaned[:2] if len(cleaned) > 2 else cleaned)


def parse_company_address(company_str: str):
    """Extract employer, location, state from combined string 'Company, City, ST ZIP'."""
    if not company_str:
        return None, None, None
    parts = [p.strip() for p in company_str.split(",") if p.strip()]
    employer = parts[0] if parts else company_str
    state = None
    location = company_str
    
    # Try finding state abbreviation or zip
    match = re.search(r'\b([A-Z]{2})\b(?:\s+\d{5})?', company_str.upper())
    if match:
        st = match.group(1)
        if st in STATE_ABBREV.values():
            state = st
    return employer, location, state


def load_osha_csv(filepath: Path) -> Generator[Dict[str, Any], None, None]:
    """Generator reading raw records from an OSHA CSV file."""
    filename = filepath.name
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        try:
            raw_headers = next(reader)
        except StopIteration:
            return
        headers = [h.strip() for h in raw_headers]
        
        for idx, row in enumerate(reader, start=1):
            if not row or not any(row):
                continue
            row_dict = {headers[i]: row[i].strip() if i < len(row) else "" for i in range(len(headers))}
            
            # Skip sub-header metadata rows in some summary CSVs
            date_val = row_dict.get("Date of Incident", "") or row_dict.get("EventDate", "")
            if date_val.lower().startswith("type") or "catastrophe" in date_val.lower():
                continue
                
            canonical = parse_canonical_record(filename, idx, row_dict)
            if canonical:
                yield canonical


def parse_canonical_record(filename: str, row_idx: int, d: Dict[str, str]) -> Dict[str, Any]:
    """Parse a single raw row dict into canonical internal representation."""
    desc = d.get("Final Narrative") or d.get("Preliminary Description of Incident") or d.get("Hazard Description") or ""
    if not desc:
        return None

    record_id = d.get("ID") or d.get("Inspection #") or f"{filename}_{row_idx}"
    raw_date = d.get("EventDate") or d.get("Date of Incident") or d.get("Summary Report Date") or ""

    if "January2015" in filename:
        employer = d.get("Employer")
        state = normalize_state(d.get("State"))
        city = d.get("City")
        addr1 = d.get("Address1")
        location = f"{addr1}, {city}, {state}".strip(", ") if city or state else addr1
        industry = d.get("Primary NAICS")
        event = d.get("EventTitle")
        source = d.get("SourceTitle")
        severity_info = {
            "hospitalized": d.get("Hospitalized"),
            "amputation": d.get("Amputation"),
            "loss_of_eye": d.get("Loss of Eye"),
            "nature": d.get("NatureTitle"),
            "body_part": d.get("Part of Body Title"),
            "inspection": d.get("Inspection")
        }
    else:
        comp_str = d.get("Company") or d.get("Company, City, State, ZIP") or d.get("Employer/Address of Incident")
        employer, location, state = parse_company_address(comp_str)
        industry = None
        event = None
        source = None
        fatality_cat = d.get("Fatality or Catastrophe", "Fatality")
        severity_info = {
            "fatality_or_catastrophe": fatality_cat,
            "inspection": d.get("Inspection #")
        }

    return {
        "source_dataset": filename,
        "source_record_id": str(record_id),
        "raw_date": raw_date,
        "description": desc,
        "employer": employer,
        "location": location,
        "state": state,
        "industry": industry,
        "event": event,
        "source": source,
        "severity_info": severity_info,
        "raw_data": d
    }


def load_all_osha_records(
    data_dir: Path = DATA_DIR,
    limit: int = None,
    representative_sample: bool = False,
    sample_seed: int = 42,
) -> List[Dict[str, Any]]:
    """Load OSHA records, optionally using a deterministic uniform sample.

    Representative samples avoid the misleading single-month result caused by
    taking only the first rows of a chronologically ordered CSV.
    """
    records = []
    csv_paths = sorted(glob.glob(str(Path(data_dir) / "*.csv")))

    # Prioritize the comprehensive dataset (2015-2025) if it exists
    comprehensive_path = None
    other_paths = []
    for path in csv_paths:
        if "January2015toNovember2025" in path or "2015toNovember" in path:
            comprehensive_path = path
        else:
            other_paths.append(path)

    paths = ([comprehensive_path] if comprehensive_path else []) + other_paths
    if representative_sample and limit:
        rng = random.Random(sample_seed)
        seen = 0
        for path in paths:
            for rec in load_osha_csv(Path(path)):
                seen += 1
                if len(records) < limit:
                    records.append(rec)
                else:
                    replacement = rng.randrange(seen)
                    if replacement < limit:
                        records[replacement] = rec
        return records

    for path in paths:
        for rec in load_osha_csv(Path(path)):
            records.append(rec)
            if limit and len(records) >= limit:
                return records

    return records
