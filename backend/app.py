from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import shutil
import os

# Load environment variables
load_dotenv()

app = FastAPI()

# Load embedding model


# Load Groq model
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0
)

# Store FAISS database in memory
vector_db = None

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads folder
os.makedirs("uploads", exist_ok=True)


@app.get("/")
def home():
    return {
        "message": "AI Knowledge Base Backend is Running 🚀"
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global vector_db

    # Save uploaded PDF
    file_path = os.path.join("uploads", file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Read PDF
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = text_splitter.split_text(text)
    embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001"
)

    # Create FAISS vector database
    vector_db = FAISS.from_texts(chunks, embeddings)

    # Save vector database locally
    vector_db.save_local("faiss_index")

    print("\n=========== VECTOR DATABASE ===========")
    print("✅ FAISS Vector Database Created Successfully!")
    print(f"Stored {len(chunks)} chunks.")
    print("========================================\n")

    return {
        "message": "PDF uploaded successfully",
        "filename": file.filename,
        "characters": len(text),
        "chunks": len(chunks)
    }


class Question(BaseModel):
    question: str


@app.post("/ask")
async def ask_question(data: Question):
    global vector_db

    if vector_db is None:
        return {
            "answer": "Please upload a PDF first."
        }

    # Search similar chunks
    docs = vector_db.similarity_search(
        data.question,
        k=10
    )

    context = "\n\n".join(doc.page_content for doc in docs)

    # Prompt for Groq
    prompt = f"""
You are an intelligent PDF assistant.

Use ONLY the context below to answer.

If the user asks for a summary, summarize the available context.

If the answer cannot be found in the provided context, reply:

"I couldn't find that information in the uploaded PDF."

Context:
{context}

Question:
{data.question}

Answer:
"""


    try:
        response = llm.invoke(prompt)

        return {
            "question": data.question,
            "answer": response.content
        }

    except Exception as e:
        print("\n========== GROQ ERROR ==========")
        print(type(e))
        print(e)
        print("================================")

        return {
            "error": str(e)
        }