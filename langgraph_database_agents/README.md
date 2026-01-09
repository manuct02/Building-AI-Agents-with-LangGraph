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