"""Configura opciones comunes de pytest."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Añade el flag opcional para pruebas con SQL Server."""

    parser.addoption(
        "--run-sqlserver",
        action="store_true",
        default=False,
        help="Ejecuta los tests de integración contra SQL Server.",
    )
