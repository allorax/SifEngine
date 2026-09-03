from app.data.cleaner import normalize_date, clean_records
from app.data.loader import parse_canonical_record, normalize_state, parse_company_address


def test_normalize_state():
    assert normalize_state("CALIFORNIA") == "CA"
    assert normalize_state("TX") == "TX"
    assert normalize_state("NEW YORK") == "NY"
    assert normalize_state(None) is None


def test_parse_company_address():
    emp, loc, st = parse_company_address("L.B. Thompson Inc., Tampa, FL 33610")
    assert emp == "L.B. Thompson Inc."
    assert st == "FL"


def test_normalize_date():
    assert normalize_date("1/1/2015") == "2015-01-01"
    assert normalize_date("09/20/09") == "2009-09-20"
    assert normalize_date("2021-05-15") == "2021-05-15"
    assert normalize_date("invalid") is None


def test_clean_records():
    raw_data = [
        {
            "source_dataset": "test.csv",
            "source_record_id": "1",
            "raw_date": "1/1/2015",
            "description": "Worker fell from a 20-foot ladder while painting.",
            "employer": "ABC Construction",
            "state": "CA"
        },
        {
            "source_dataset": "test.csv",
            "source_record_id": "2",
            "raw_date": "1/1/2015",
            "description": "Worker fell from a 20-foot ladder while painting.",
            "employer": "ABC Construction",
            "state": "CA"
        },
        {
            "source_dataset": "test.csv",
            "source_record_id": "3",
            "raw_date": "",
            "description": "",
            "employer": "Empty Corp"
        }
    ]

    cleaned, profile = clean_records(raw_data)
    assert len(cleaned) == 1
    assert profile["total_records"] == 3
    assert profile["valid_records"] == 1
    assert profile["invalid_records"] == 2
    assert profile["missing_descriptions"] == 1
