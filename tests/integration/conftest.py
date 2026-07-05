"""Marca los tests de integración como opcionales."""

import pytest


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Salta la carpeta de integración si falta el flag explícito."""

    if config.getoption("--run-sqlserver"):
        return

    skip_sqlserver = pytest.mark.skip(
        reason="requiere --run-sqlserver",
    )

    for item in items:
        if "tests/integration" in str(item.fspath):
            item.add_marker(skip_sqlserver)
