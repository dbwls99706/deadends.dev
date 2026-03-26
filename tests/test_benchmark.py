"""Tests for benchmarks.run_benchmark."""


from benchmarks.run_benchmark import evaluate_match, load_scenarios


def test_load_scenarios():
    """Scenarios file loads and contains expected entries."""
    scenarios = load_scenarios()
    assert len(scenarios) == 20
    assert all("error_message" in s for s in scenarios)
    assert all("expected_domain" in s for s in scenarios)


def test_evaluate_match_domain():
    """Domain matching works correctly."""
    scenario = {
        "expected_domain": "python",
        "correct_workaround_keywords": ["venv"],
        "known_dead_end_keywords": ["sudo"],
    }
    match_good = {"domain": "python", "workarounds": [], "dead_ends": []}
    match_bad = {"domain": "node", "workarounds": [], "dead_ends": []}

    assert evaluate_match(scenario, match_good)["domain_match"] is True
    assert evaluate_match(scenario, match_bad)["domain_match"] is False


def test_evaluate_match_workaround_hit():
    """Workaround keyword matching works."""
    scenario = {
        "expected_domain": "python",
        "correct_workaround_keywords": ["venv", "pip install"],
        "known_dead_end_keywords": [],
    }
    match = {
        "domain": "python",
        "workarounds": [{"action": "Create venv", "how": "python -m venv .venv"}],
        "dead_ends": [],
    }
    result = evaluate_match(scenario, match)
    assert result["workaround_hit"] is True


def test_evaluate_match_dead_end_hit():
    """Dead end keyword matching works."""
    scenario = {
        "expected_domain": "python",
        "correct_workaround_keywords": [],
        "known_dead_end_keywords": ["sudo pip"],
    }
    match = {
        "domain": "python",
        "workarounds": [],
        "dead_ends": [{"action": "sudo pip install", "why_fails": "breaks packages"}],
    }
    result = evaluate_match(scenario, match)
    assert result["dead_end_hit"] is True


def test_evaluate_match_no_hits():
    """No hits when keywords don't match."""
    scenario = {
        "expected_domain": "python",
        "correct_workaround_keywords": ["xyz123"],
        "known_dead_end_keywords": ["abc456"],
    }
    match = {
        "domain": "python",
        "workarounds": [{"action": "something else", "how": "other"}],
        "dead_ends": [{"action": "different", "why_fails": "nope"}],
    }
    result = evaluate_match(scenario, match)
    assert result["workaround_hit"] is False
    assert result["dead_end_hit"] is False


def test_scenarios_have_required_fields():
    """Every scenario has all required fields."""
    scenarios = load_scenarios()
    required = {"id", "error_message", "expected_domain",
                "correct_workaround_keywords", "known_dead_end_keywords"}
    for s in scenarios:
        assert required.issubset(s.keys()), f"Missing fields in {s.get('id', '?')}"
