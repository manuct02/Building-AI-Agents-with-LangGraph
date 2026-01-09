from typing import List
import sqlalchemy
from sqlalchemy.engine.base import Engine
from sqlalchemy import text
from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig

@tool
def list_tables_tool(config: RunnableConfig)->List[str]:
    """
    List all tables in database
    """

    db_engine: Engine= config.get("configurable", {}).get("db_engine")
    inspector= sqlalchemy.inspect(db_engine)

    return inspector.get_table_names()

@tool
def get_table_schema_tool(table_name:str, config: RunnableConfig)->List[str]:
    """
    Coge la información del schema sobre la tabla y devuelve una lista de diccionarios.
    - "name" es el nombre de la columna
    - "type" es el tipo de columna
    - "nullable" es si la columna es anulable o no
    - "default" es el valor predeterminado de la columna
    - "prmary_key" es si la columna es primaria o no
    """
    db_engine: Engine= config.get("configurable", {}).get("db_engine")
    inspector = sqlalchemy.inspect(db_engine)

    return inspector.get_columns(table_name)

@tool
def execute_sql_tool(query: str, config: RunnableConfig)-> int:
    """
    Execute a SQL query and return the results
    """
    db_engine:Engine = config.get("configurable", {}).get("db_engine")
    with db_engine.begin() as connection:
        answer= connection.execute(text(query)).fetchall()
    return answer
