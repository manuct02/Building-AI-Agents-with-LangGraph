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
    

