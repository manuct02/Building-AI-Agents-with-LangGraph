import mlflow
from mlflow import log_params, log_metrics
from typing import List, Dict
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import MessagesState
from langchain_core.prompts import ChatPromptTemplate
from IPython.display import Image, display
from ragas import evaluate
from datasets import Dataset
import os

from dotenv import load_dotenv
load_dotenv()

llm= ChatOpenAI(model= "gpt-4o-mini", temperature= 0.0, base_url= os.getenv("OPENAI_BASE_URL"), api_key= os.getenv("OPENAI_API_KEY"))

embeddings_fn= OpenAIEmbeddings(model= "text-embedding-3-small")

# para evaluar

llm_judge= ChatOpenAI(model= "gpt-4o", temperature= 0.0, base_url= os.getenv("OPENAI_BASE_URL"), api_key= os.getenv("OPENAI_API_KEY"))


# 2. MLFlow

mlflow.set_experiment("udacity")
with mlflow.start_run(run_name="l4_exercise_02") as run:
    log_params(
        {
            "embeddings_model":embeddings_fn.model,
            "llm_model": llm.model_name,
            "llm_judge_model": llm_judge.model_name,
        }
    )
    print(run.info)

mlflow_run_id= run.info.run_id
mflow_client= mlflow.tracking.MlflowClient()
mflow_client.get_run(mlflow_run_id)

# 3. Cargar y procesar documentos

vector_store= Chroma( collection_name= "udacity", embedding_function=embeddings_fn)

file_path= "./compact-guide-to-large-language-models.pdf"
loader= PyPDFLoader(file_path=file_path)

pages= []
for page in loader.load():
    pages.append(page)

text_splitter= RecursiveCharacterTextSplitter(chunk_size= 1000, chunk_overlap= 200)
all_splits= text_splitter.split_documents(pages)
_= vector_store.add_documents(documents=all_splits)

# 4. Define el esquema del estado

class State(MessagesState):
    run_id: str
    question: str
    ground_truth: str
    documents: List[Document]
    answer: str
    evaluation: Dict

# 5. Nodos del Rag
def retrieve(state: State):
    question = state["question"]
    retrieved_docs = vector_store.similarity_search(question)
    return {"documents": retrieved_docs}

def augment(state: State):
    question = state["question"]
    documents = state["documents"]
    docs_content = "\n\n".join(doc.page_content for doc in documents)

    template= ChatPromptTemplate([("system", "You are an assistant for question-answering tasks."),
        ("human", "Use the following pieces of retrieved context to answer the question. "
                "If you don't know the answer, just say that you don't know. " 
                "Use three sentences maximum and keep the answer concise. "
                "\n# Question: \n-> {question} "
                "\n# Context: \n-> {context} "
                "\n# Answer: "),
                ])
    messages= template.invoke({"context": docs_content, "question": question}).to_messages()
    return  {"messages": messages}

def generate(state: State):
    ai_message = llm.invoke(state["messages"])
    return {"answer": ai_message.content, "messages": ai_message}

def evaluate_rag(state: State):
    question= state["question"]
    documents= state["documents"]
    answer= state["answer"]
    ground_truth= state["ground_truth"]
    dataset = Dataset.from_dict(
        {
            "question": [question],
            "answer": [answer],
            "contexts": [[doc.page_content for doc in documents]],
            "ground_truth": [ground_truth]
        }
    )
    evaluation_results= evaluate(dataset=dataset, llm=llm_judge)
    print(evaluation_results)

    with mlflow.start_run(state["run_id"]):
        log_metrics({
            "faithfulness": evaluation_results["faithfulness"][0],
            "context_precision": evaluation_results["context_precision"][0],
            "context_recall":evaluation_results["context_recall"][0],
            "answer_relevancy": evaluation_results["answer_relevancy"][0]
        })
    return {"evaluation": evaluation_results}

# 6. El workflow

workflow = StateGraph(State)

workflow.add_node("retrieve", retrieve)
workflow.add_node("augment", augment)
workflow.add_node("generate", generate)
workflow.add_node("evaluate_rag", evaluate_rag)

workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "augment")
workflow.add_edge("augment", "generate")
workflow.add_edge("generate", "evaluate_rag")
workflow.add_edge("evaluate_rag", END)

graph = workflow.compile()

display(
    Image(
        graph.get_graph().draw_mermaid_png()
    )
)


# 7. Invocar el workflow con una query

reference = [
    {
        "question": "What are Open source models?",
        "ground_truth": "Open-source models are AI or machine learning " 
                        "models whose code, architecture, and in some cases, " 
                        "training data and weights, are publicly available for " 
                        "use, modification, and distribution. They enable " 
                        "collaboration, transparency, and innovation by allowing " 
                        "developers to fine-tune, deploy, or improve them without " 
                        "proprietary restrictions.",
    }
]

output = graph.invoke(
    {
        "question": reference[0]["question"],
        "ground_truth": reference[0]["ground_truth"],
        "run_id": mlflow_run_id
    }
)

print(mflow_client.get_run(mlflow_run_id))