# Create a Text2SQL ReAct Agent

En este ejercicio crearemos un ReAct-based agent capaz de interpretar el preguntas en lenguaje natural y convertirla en queries de SQL para extraer datos de la database. Este tipo de agentes construye el puente entre el lenguaje humano y los datos estructurados.

### Escenario

Trabajaremos en un asistente conversaconal de análisis que permita a l usuario hacer queries sobre datos de negocio en inglés plano. 

Los datos están almacenados en una base de datos relacional. Para acceder a éstos, nuestro asistente deberá convertir la query del usuario en un comando válido de SQL. Necesita además **razonar sobre la mejor manera de llegar a la respuesta** y **ejecutar la query** de forma segura.

Para conseguir lo último, usaremos el ReAct pattern, donde nuestro agente pueda, tanto **pensar** (razonamiento step-by-step sobre la query) como **actuar** (ruear tools como *SQL engine*) a la hora de resolver la task.

### Challenge

Construimos un asistente Text2SQL para un Panel de Ventas. El agente debería:

- Parsear las preguntas del usuario
- Identificar las tablas y columnas relevantes
- Generar la SQL query correspondiente
- Ejecutar la query y devolver el resultado

## Resumen: Workflow del agente Text2SQL con LangGraph

### 1. Tooling y setup del entorno 

- Varias tools de interacción con la base de datos ya están predefinidas:
  - `list_tables_tool`
  - `get_table_schema_tool`
  - `execute_sql_tool`
- Hay una database (100 filas) precargada para usar en las queries.
- El LLM de OpenAI se inicializa con `load_dotenv()` para manejar la API de forma segura.

### 2. State Definition

- Una clase `State` se crea ampliando `MessageGraphState`, añadiendo un simple campo:
- `user_query:str`
- Este estado guarda la pregunta del usuario así como el historial de mensajes a través de la ejecución del graph.
```python
class State(MessageGraphState):
    user_query: str
```

### 3. LLM Tool Binding

- Las tres tool de SQL están ligadas al LLM usando la tool de abstacción de LangChain.
- Un nuevo nodo `dba_tools` se añade al grafo para la invocación de las tools.
```python
dba_llm_with_tools = llm.bind_tools([list_tables_tool, get_table_schema_tool, execute_sql_tool])
workflow.add_node("dba_tools", dba_llm_with_tools)
```
### 4. Construcción de los nodos
- Un message-building node inicializa el prompt del sistema e inyecta la query del usuario como un mensaje.
- El `dba_agent` node usa este historial de mesnajes e invoca al LLM para generar la siguiente respuesta:

```python
def messages_builder(state):
    return {"messages": [SystemMessage(...), HumanMessage(content=state.user_query)]}
```

- Se añaden estos dos nodos (`messages_builder` y `dba_agent`) al workflow.

### 5. Routing Logic

- Una función de routing examina el mensaje más reciente:
  - Si el mensaje incluye `tool_call`, el workflow routea hacia `dba_tools`.
  - De otra forma, termina.

- Los resultados tras la ejecución de la tool loopean back hacia el agente para futuros razonamientos si es necesario.

```python
def router(state):
    last_msg= state["messages"][-1]
    return "dba_tools" if last_msg.tool_calls else "end"
```

- Edges se definen para formar un bucle:
`start -> messages_builder -> dba_agent -> dba_tools -> dba_agent`, hasta que no se usen tools.

### 6. Ejecución y testing
- EL workflow se compila y visualiza.
- Una query de test se inyecta: *"How many Dell XPS 15 were sold?"*
- El sistema procesa la query siguiendo los siguientes pasos:
  - a. Lista las tablas disponibles
  - b. Recupera el esquema para la tabla relevante (`sales`)
  - c. Genera y ejecuta la query:
  ```SQL
  SELECT SUM(quantity) FROM sales WHERE model = 'Dell XPS 15' ;
  ```
  - Devuelve un resultado vía un AI message.

- Los logs deben confirmar el uso de las tools y pasos intermedios , asegurando el funcionamiento del workflow como debe ser.

## Toolkit

Por lo visto las herramientas están creadas en otro script, vamos a construirlas en el `sql_toolkit.py`.
Cambié la base de datos por una musical.

## Solución


### Las herramientas

```python 
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
``` 

Y el Agente se encuentra en `text2sql_agent.py`

```python
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display
from sqlalchemy import create_engine
from sql_toolkit import (list_tables_tool, execute_sql_tool, get_table_schema_tool)
import os
from pathlib import Path

from dotenv import load_dotenv

# 1. Cargamos la API

load_dotenv()

llm= ChatOpenAI(model="gpt-4o-mini", temperature= 0.0, api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))


# 2. Inicializamos el grafo

class State(MessagesState):
    user_query: str

workflow= StateGraph(State)

# 3. Definimos las herramientas disponibles

dba_tools= [list_tables_tool, get_table_schema_tool, execute_sql_tool]
workflow.add_node("dba_tools", ToolNode(dba_tools))
dba_llm= llm.bind_tools(dba_tools, tool_choice="auto")

# 4. Los nodos del agente

def messages_builder(state: State):
    dba_sys_msg= ("You are a Sr. SQL developer tasked with generating SQL queries. Perform the following steps:\n"
        "First, find out the appropriate table name based on all tables. "
        "Then get the table's schema to understand the columns. "
        "With the table name and the schema, generate the ANSI SQL query you think is applicable to the user question. "
        "Finally, use a tool to execute the above SQL query and output the result based on the user question.")
    messages= [SystemMessage(dba_sys_msg), HumanMessage(state["user_query"])]
    return{"messages": messages}

def dba_agent(state:State):
    ai_message= dba_llm.invoke(state["messages"])
    ai_message.name= "dba_agent"
    return {"messages": ai_message}

workflow.add_node("messages_builder", messages_builder)
workflow.add_node("dba_agent", dba_agent)

# 5. Edges

def should_continue(state: State):
    messages= state["messages"]
    last_message= messages[-1]
    if last_message.tool_calls:
        return "dba_tools"
    return END

workflow.add_edge(START, "messages_builder")
workflow.add_edge("messages_builder", "dba_agent")
workflow.add_conditional_edges(source="dba_agent", path= should_continue, path_map=["dba_tools", END])
workflow.add_edge("dba_tools", "dba_agent")

react_graph= workflow.compile()

db_path = os.path.join(os.path.dirname(__file__), "Chinook_Sqlite.sqlite")
db_engine = create_engine(f"sqlite:///{db_path}")
config = {"configurable":{"db_engine":db_engine}}
inputs = {"user_query": "Show me 5 customer names"}

# Verificar conexión
print(f"Database path: {db_path}")
print(f"File exists: {os.path.exists(db_path)}")

# Test rápido de la BD
from sqlalchemy import inspect
inspector = inspect(db_engine)
print(f"Tables in database: {inspector.get_table_names()}")

result = react_graph.invoke(input=inputs, config=config)

# AQUÍ: Imprimir correctamente los mensajes
print("\n=== MESSAGES ===")
for m in result["messages"]:
    m.pretty_print()
```