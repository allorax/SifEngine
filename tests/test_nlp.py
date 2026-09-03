from app.nlp.extractors import extract_safety_info


def test_extract_safety_info_loto():
    text = "Worker was performing servicing on conveyor belt without locking out breaker. Hand was caught in moving gear."
    info = extract_safety_info(text)
    assert "Equipment Isolation / LOTO" in info["hazards"]
    assert "conveyor" in info["equipment"]
    assert len(info["unsafe_actions"]) > 0 or len(info["unsafe_conditions"]) > 0 or len(info["people_involved"]) > 0


def test_extract_safety_info_fall():
    text = "Roofing contractor fell 30 feet from scaffold structure. Suffered fatal broken neck."
    info = extract_safety_info(text)
    assert "Falls / Working at Height" in info["hazards"]
    assert "scaffold" in info["equipment"]
    assert "fatal" in info["potential_consequence"] or "broken" in info["potential_consequence"]
