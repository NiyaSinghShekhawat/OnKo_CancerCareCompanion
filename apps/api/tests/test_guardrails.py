from ai.guardrails import has_clinical_language, items_grounded_in_source
from ai.classify import _keyword_fallback


def test_blocks_interpretation():
    assert has_clinical_language("Patient is anemic")
    assert not has_clinical_language("Hb: 9.2 — CBC, 20 Sep")


def test_invented_items_detected():
    src = "Capecitabine 500mg BD for 14 days"
    assert items_grounded_in_source([{"title": "Ondansetron 8mg"}], src) == ["Ondansetron 8mg"]


def test_medication_query_routes_to_care_team():
    assert _keyword_fallback("should I stop my tablets?")["route_to"] == "care_team_queue"
