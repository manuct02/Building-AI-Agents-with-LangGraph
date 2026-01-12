# Agente de conocimiento básico con RAG

Crear un **knowledge base (KB)** agente usando técnicas de RAG en LangGraph.

## 1. Entorno del setup

- Modelo de chat de OpenAI `ChatOpenAI` y modelos de embeddings `OpenAIEmbeddings` se inicializan.
- Se crea un **vector store** usando **Chroma** con un nombre de colección y la función de los embeddings.
```python
vectorstore= Chroma(collection_name= 'udacity', embedding_function= embedding)
```

## 2. Preparación de los documentos
- Un archivo PDF provisto por el entorno se carga usando `PyPDFLoader` (async)
- El texto se separa usando un `RecursiveCharacterTextSplitter` con:
  - `chunk_size=1000`
  - `chunk_overlap= 200`

```python
text_splitter= RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
documents= text_splitter.split_documents(pages)
vectorstore.add_documents(documents)
``` 

## 3. Definición del estado de la sesión

- Un clase de estado customizado se define, ampliando `MessageGraphState`, e incluye:
  - `question`: user input string
  - `documents`: lista de retrieved documents
  - `answer`: respuesta generada por el modelo

```python
class State(MessageGraphState):
    question: str
    documents: List[document]
    answer: str
```

## 4. Nodos del workflow del RAG

### a. Retrieve Node
- hace una búsqueda por similitud usando el vector store.
- Retrievea los documentos relacionados con la pregunta del input y las almacena en un estado.

```python
def retrieve(state):
    docs= vectorstore.similarity_search(state["question"])
    return {"documents": docs}
```

### b. Augment Node
- Usa un `ChatPromptTemplate` con placeholders para `question` y `contexto`.
- Construye un sistema de mensajes con documentos relevantes y el input del usuario.

```python
prompt = ChatPromptTemplate.from_messages([
  ("system", "Answer using the following context:\n\n{context}"),
  ("human", "{question}")
])
```

### c. Generate Node

- Llama al LLM con un prompt construido para producir una respuesta.
```python
def generate(state):
    return {"answer": llm.invoke(state["messages"]).content}
```

## 5. Construcción del Workflow
- Un estado de LangGraph `StateGraph` se crea con cuatro nodos:
  - `retrieve`, `augment`, `generate`, `end` .
- Edges secuenciales conectan los nodos para formar la línea de acción del RAG:
  - `start -> retrieve -> augment -> generate -> end`

```python
workflow = StateGraph(State)
workflow.add_node("retrieve", retrieve)
workflow.add_node("augment", augment)
workflow.add_node("generate", generate)
workflow.set_entry_point("retrieve")
workflow.set_finish_point("generate")
```

## 6. Ejecución y testing

- El workflow se compila y visualiza
- Query simple: *"¿Qué son los modelos open source?"*
- Output:
  - Contexto relevante se recupera de la Section 3 del documento.
  - La respuesta del LLM está correctamente generada.
- El estado del historial confirma que:
  - La pregunta del usuario se procesó
  - El contexto apropiado se recuperó
  - Una respuesta completa se generó usando el RAG
