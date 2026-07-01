import os
import sys

import pyodbc
from dotenv import load_dotenv


load_dotenv()


def main() -> None:
    host = os.getenv("SQLSERVER_HOST")
    port = os.getenv("SQLSERVER_PORT")
    database = os.getenv("SQLSERVER_DATABASE")
    user = os.getenv("SQLSERVER_USER")
    password = os.getenv("SQLSERVER_PASSWORD")
    driver = os.getenv("SQLSERVER_DRIVER")

    required = {
        "SQLSERVER_HOST": host,
        "SQLSERVER_PORT": port,
        "SQLSERVER_DATABASE": database,
        "SQLSERVER_USER": user,
        "SQLSERVER_PASSWORD": password,
        "SQLSERVER_DRIVER": driver,
    }

    missing = [name for name, value in required.items() if not value]

    if missing:
        raise ValueError(
            f"Faltan variables en el archivo .env: {', '.join(missing)}"
        )

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={host},{port};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=10;"
    )

    try:
        with pyodbc.connect(connection_string) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT
                    DB_NAME() AS database_name,
                    @@SERVERNAME AS server_name,
                    @@VERSION AS server_version
                """
            )

            row = cursor.fetchone()

            print("Conexión correcta")
            print(f"Base de datos: {row.database_name}")
            print(f"Servidor: {row.server_name}")
            print(f"Versión: {row.server_version}")

    except pyodbc.Error as error:
        print("No fue posible conectar con SQL Server.")
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()