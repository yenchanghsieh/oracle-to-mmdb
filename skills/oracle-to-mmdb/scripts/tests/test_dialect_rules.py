from dialect_rules import RULES, rules_by_safety


def test_safe_rules_include_simple_null_and_date_conversions():
    safe = rules_by_safety("safe_auto_convert")
    assert "NVL_SIMPLE" in safe
    assert "SYSDATE" in safe


def test_complex_rules_are_not_safe_auto_convert():
    assert RULES["CONNECT_BY"]["safety"] == "do_not_auto_convert"
    assert RULES["MERGE_INTO"]["safety"] == "needs_review"
