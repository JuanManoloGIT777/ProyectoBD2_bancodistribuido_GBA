import psycopg2
from psycopg2.extras import RealDictCursor


def obtener_conexion():
    """
    Crea y retorna una conexión a PostgreSQL.
    Si hay error, retorna None.
    """

    try:
        conexion = psycopg2.connect(
            host="localhost",
            port="5432",
            database="banco_distribuido",
            user="postgres",
            password="Postgres123",
            cursor_factory=RealDictCursor
        )

        return conexion

    except Exception as error:
        print("Error al conectar con PostgreSQL:", error)
        return None

        