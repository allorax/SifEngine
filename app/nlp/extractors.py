import re
from typing import Dict, Any, List
from app.nlp.taxonomy import SAFETY_TAXONOMY, EQUIPMENT_KEYWORDS, CONSEQUENCE_KEYWORDS

_spacy_nlp = None


def get_spacy_nlp():
    """Lazy load spaCy model if available."""
    global _spacy_nlp
    if _spacy_nlp is None:
        try:
            import spacy
            _spacy_nlp = spacy.load("en_core_web_sm")
        except Exception:
            _spacy_nlp = False
    return _spacy_nlp


def extract_safety_info(text: str) -> Dict[str, Any]:
    """Extract safety entities, hazards, equipment, actions, and consequences from narrative."""
    if not text:
        return {}

    info = _extract_rule_info(text)
    nlp = get_spacy_nlp()
    if nlp:
        try:
            info["activity"] = _extract_activity(nlp(text[:500]))
        except Exception:
            pass
    return info


def extract_safety_info_batch(texts: List[str], batch_size: int = 128) -> List[Dict[str, Any]]:
    """Extract safety data in batches, using spaCy's efficient ``pipe`` API."""
    results = [_extract_rule_info(text) if text else {} for text in texts]
    nlp = get_spacy_nlp()
    if not nlp:
        return results
    try:
        for info, doc in zip(results, nlp.pipe((text[:500] for text in texts), batch_size=batch_size)):
            if info:
                info["activity"] = _extract_activity(doc)
    except Exception:
        # Rule extraction remains complete if the optional spaCy pass fails.
        pass
    return results


def _extract_rule_info(text: str) -> Dict[str, Any]:
    """Run deterministic taxonomy and keyword extraction for one narrative.

    Hazard assignment now ranks categories by the number of keyword hits and
    only keeps the single best-matching (primary) category.  This prevents a
    single report from being counted towards many broad categories and
    eliminates the main source of duplicate cluster labels.
    """

    text_lower = text.lower()
    
    # 1. Identify matched hazards from taxonomy — rank by keyword hit count
    #    so each report gets only the single most specific category.
    category_scores: list[tuple[str, int]] = []
    for category, keywords in SAFETY_TAXONOMY.items():
        hit_count = sum(1 for kw in keywords if kw in text_lower)
        if hit_count > 0:
            category_scores.append((category, hit_count))

    # Sort descending by hit count; keep only the best match
    category_scores.sort(key=lambda x: x[1], reverse=True)
    hazards = [category_scores[0][0]] if category_scores else []

    # 2. Identify equipment involved
    equipment = [eq for eq in EQUIPMENT_KEYWORDS if eq in text_lower]

    # 3. Identify potential consequences
    consequences = [c for c in CONSEQUENCE_KEYWORDS if c in text_lower]

    # 4. Extract people involved
    people = []
    people_terms = ["victim", "worker", "employee", "operator", "driver", "co-worker", "guard", "decedent", "contractor"]
    for p in people_terms:
        if p in text_lower:
            people.append(p)

    # 5. Extract unsafe actions & conditions via pattern rules
    unsafe_actions = []
    if any(k in text_lower for k in ["not wearing", "seatbelt", "no ppe", "harness", "failed to lock", "unsecured"]):
        unsafe_actions.append("Lack of proper PPE or safety restraint")
    if "bypass" in text_lower or "guarding removed" in text_lower:
        unsafe_actions.append("Bypassing safety guards/protocols")

    unsafe_conditions = []
    if any(k in text_lower for k in ["collapse", "collapsed", "broke", "broken", "leak", "live wire", "unstable", "slippery"]):
        unsafe_conditions.append("Structural failure or hazardous environment")

    return {
        "hazards": hazards,
        "equipment": equipment,
        "activity": None,
        "unsafe_actions": unsafe_actions,
        "unsafe_conditions": unsafe_conditions,
        "potential_consequence": consequences,
        "people_involved": people
    }


def _extract_activity(doc) -> str | None:
    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB" and not token.is_stop]
    return f"Performing actions involving {', '.join(verbs[:3])}" if verbs else None
