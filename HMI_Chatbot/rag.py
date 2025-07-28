from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import shutil
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from datetime import datetime
import pytz

timezone = pytz.timezone('Asia/Kolkata')


current_time = datetime.now(timezone)

app = FastAPI()

# Use fast embedding model on GPU
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cuda"}  # Use GPU
)

print("🔍 Embedding model device:", embeddings.client.device)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"📥 Received {request.method} {request.url}")
    response = await call_next(request)
    print(f"📤 Responded with {response.status_code}")
    return response

@app.post("/rag-query")
async def query_rag(query: str = Form(...), pdf_file: UploadFile = Form(...)):
    print("✅ RAG endpoint called")
    print("Called at:", current_time.strftime('%Y-%m-%d %H:%M:%S'))
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(pdf_file.file, tmp)
            tmp_path = tmp.name
        print("Loaded Now")
        loader = PyPDFLoader(tmp_path)
        pages = loader.load()

        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        print("Loaded 2")
        splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
        docs = splitter.split_documents(pages)
        print("Loaded 3")
        vectordb = Chroma.from_documents(docs, embedding=embeddings)
        retriever = vectordb.as_retriever()
        print("Loaded 4")
        llm = Ollama(model="mistral")
        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
        result = qa_chain.invoke(query)
        print(result)
        return JSONResponse(content={"answer": result})

    except Exception as e:
        import traceback
        traceback.print_exc()  # 🔍 Shows full error in server logs
        return JSONResponse(content={"error": str(e)}, status_code=500)

