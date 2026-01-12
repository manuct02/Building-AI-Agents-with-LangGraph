from typing import List
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import MessagesState
from IPython.display import Image, display
import asyncio
import os


from dotenv import load_dotenv
load_dotenv()

llm= ChatOpenAI(model= "gpt-4o-mini", temperature= 0.0, base_url= os.getenv("OPENAI_BASE_URL"), api_key= os.getenv("OPENAI_API_KEY"))

embeddings_fn= OpenAIEmbeddings(model= "text-embedding-3-small")

# 2. Cargar y procesar documentos

vector_store= Chroma(collection_name= "udacity", embedding_function=embeddings_fn)
file_path= "./compact-guide-to-large-language-models.pdf"
loader= PyPDFLoader(file_path=file_path)

async def load_pages():
    pages= []
    async for page in loader.alazy_load():
        pages.append(page)
    return pages

pages= asyncio.run(load_pages())

text_splitter= RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap= 200)
all_splits= text_splitter.split_documents(pages)
_= vector_store.add_documents(documents=all_splits)

# 3. Definir el esquema del estado

class State(MessagesState):
    question: str
    documents: List[Document]
    answer: str

# 4. Nodos del RAG

def retrieve(state: State):
    question= state["question"]
    retrieved_docs= vector_store.similarity_search(question)
    return{"documents": retrieved_docs}

def augment(state:State):
    question= state["question"]
    documents= state["documents"]
    docs_content= "\n\n".join(doc.page_content for doc in documents)

    template= ChatPromptTemplate([("system", "You are an assistant for question-answering tasks."),
        ("human", "Use the following pieces of retrieved context to answer the question. "
                "If you don't know the answer, just say that you don't know. " 
                "Use three sentences maximum and keep the answer concise. "
                "\n# Question: \n-> {question} "
                "\n# Context: \n-> {context} "
                "\n# Answer: "),
                ])
    messages= template.invoke({"context":docs_content, "question": question}).to_messages()
    return {"messages": messages}

def generate(state: State):
    ai_message= llm.invoke(state["messages"])
    return {"answer": ai_message.content, "messages": ai_message}

# 5. Construir el workflow de LangGraph

workflow= StateGraph(State)

workflow.add_node("retrieve", retrieve)
workflow.add_node("augment", augment)
workflow.add_node("generate", generate)

workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "augment")
workflow.add_edge("augment", "generate")
workflow.add_edge("generate", END)

graph= workflow.compile()
display(Image(graph.get_graph().draw_mermaid_png()))

# 6. Invocar el workflow con una query

output= graph.invoke({"question": "Qué son los modelos Open source?"})

for message in output["messages"]:
    message.pretty_print()