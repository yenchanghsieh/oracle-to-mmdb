from classify_sql import classify_statement, extract_table_names


def test_extract_table_names_from_common_dml():
    sql = "SELECT * FROM ORDERS o JOIN PAYMENT p ON p.ORDER_ID = o.ID WHERE ROWNUM <= 10"
    assert extract_table_names(sql) == ["ORDERS", "PAYMENT"]


def test_classifies_mariadb_when_all_tables_migrated():
    result = classify_statement("SELECT * FROM ORDERS WHERE ROWNUM <= 10", {"ORDERS"}, {"INVOICE"})
    assert result["classification"] == "MARIADB"
    assert result["tables"] == ["ORDERS"]


def test_classifies_oracle_when_all_tables_are_oracle_only():
    result = classify_statement("SELECT * FROM INVOICE", {"ORDERS"}, {"INVOICE"})
    assert result["classification"] == "ORACLE"


def test_classifies_cross_db_for_mixed_tables():
    result = classify_statement("SELECT * FROM ORDERS o JOIN INVOICE i ON i.ORDER_ID = o.ID", {"ORDERS"}, {"INVOICE"})
    assert result["classification"] == "CROSS_DB"


def test_unresolved_table_blocks_editing():
    result = classify_statement("SELECT * FROM UNKNOWN_TABLE", {"ORDERS"}, {"INVOICE"})
    assert result["classification"] == "UNRESOLVED"
    assert result["editable"] is False
