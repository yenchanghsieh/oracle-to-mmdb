RULES = {
    "NVL_SIMPLE": {
        "oracle": "NVL(x, y)",
        "mariadb": "IFNULL(x, y)",
        "safety": "safe_auto_convert",
        "note": "Safe for simple two-argument expressions. Review nested calls manually.",
    },
    "SYSDATE": {
        "oracle": "SYSDATE",
        "mariadb": "NOW()",
        "safety": "safe_auto_convert",
        "note": "Use NOW(6) if fractional seconds are required.",
    },
    "ROWNUM_LIMIT": {
        "oracle": "ROWNUM <= n",
        "mariadb": "LIMIT n",
        "safety": "needs_review",
        "note": "Preserve ORDER BY semantics before converting pagination.",
    },
    "DECODE": {
        "oracle": "DECODE(expr, ...)",
        "mariadb": "CASE WHEN ... END",
        "safety": "needs_review",
        "note": "Oracle NULL and type coercion behavior must be checked.",
    },
    "MERGE_INTO": {
        "oracle": "MERGE INTO",
        "mariadb": "INSERT ... ON DUPLICATE KEY UPDATE",
        "safety": "needs_review",
        "note": "Requires key/index validation.",
    },
    "CONNECT_BY": {
        "oracle": "CONNECT BY",
        "mariadb": "WITH RECURSIVE",
        "safety": "do_not_auto_convert",
        "note": "Requires semantic rewrite and manual review.",
    },
}


def rules_by_safety(safety: str) -> dict[str, dict[str, str]]:
    return {name: rule for name, rule in RULES.items() if rule["safety"] == safety}
