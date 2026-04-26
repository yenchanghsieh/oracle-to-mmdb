from pathlib import Path

from discover import discover_project


FIXTURE = Path(__file__).parent / "fixtures" / "spring-app"


def test_discover_detects_oracle_config_and_persistence_layers():
    report = discover_project(FIXTURE)
    assert report["persistence_layers"]["jpa"] is True
    assert report["persistence_layers"]["mybatis"] is True
    assert report["persistence_layers"]["jdbc_template"] is False
    assert "pom.xml" in report["oracle_candidates"]
    assert "src/main/resources/application.yml" in report["oracle_candidates"]


def test_discover_finds_entities_repositories_and_mappers():
    report = discover_project(FIXTURE)
    assert report["entities"] == [
        {
            "file": "src/main/java/com/example/entity/OrderEntity.java",
            "entity": "OrderEntity",
            "table": "ORDERS",
        }
    ]
    assert "src/main/java/com/example/repository/OrderRepository.java" in report["repositories"]
    assert "src/main/resources/mapper/OrderMapper.xml" in report["mybatis_mappers"]
