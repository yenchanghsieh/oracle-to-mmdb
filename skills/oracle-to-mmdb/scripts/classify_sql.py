import re


TABLE_PATTERN = re.compile(r"\b(?:FROM|JOIN|INTO|UPDATE)\s+([A-Za-z_][\w$#.]*)", re.IGNORECASE)


def _normalize_table(name: str) -> str:
    return name.split(".")[-1].strip('"').upper()


def extract_table_names(sql: str) -> list[str]:
    tables = {_normalize_table(match.group(1)) for match in TABLE_PATTERN.finditer(sql)}
    return sorted(tables)


def classify_statement(sql: str, migrated_tables: set[str], oracle_tables: set[str]) -> dict:
    migrated = {table.upper() for table in migrated_tables}
    oracle = {table.upper() for table in oracle_tables}
    tables = extract_table_names(sql)
    table_set = set(tables)
    unresolved = sorted(table_set - migrated - oracle)
    if not tables or unresolved:
        classification = "UNRESOLVED"
    elif table_set <= migrated:
        classification = "MARIADB"
    elif table_set <= oracle:
        classification = "ORACLE"
    else:
        classification = "CROSS_DB"
    return {
        "classification": classification,
        "tables": tables,
        "unresolved_tables": unresolved,
        "editable": classification == "MARIADB",
    }
