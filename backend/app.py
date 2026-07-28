import os
import shutil
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel
from pypdf import PdfReader

# Load environment variables
load_dotenv()

app = FastAPI()

# Load Groq model
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0
)

# Load Hugging Face embedding model ONLY ONCE
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Store FAISS database in memory
vector_db = None

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Change to your Vercel URL later
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

    try:
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

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )

        chunks = text_splitter.split_text(text)

        # Create FAISS vector store
        vector_db = FAISS.from_texts(
            chunks,
            embeddings
        )

        vector_db.save_local("faiss_index")

        print("\n=========== VECTOR DATABASE ===========")
        print("✅ FAISS Vector Database Created Successfully!")
        print(f"Stored {len(chunks)} chunks.")
        print("========================================\n")

        return {
            "message": "PDF uploaded successfully",
            "filename": file.filename,
            "characters": len(text),
            "chunks": len(chunks),
        }

    except Exception as e:
        print("\n========== EMBEDDING ERROR ==========")
        print(type(e))
        print(e)
        print("=====================================\n")

        return {
            "message": "Failed to create embeddings.",
            "error": str(e)
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

    docs = vector_db.similarity_search(
        data.question,
        k=10
    )

    context = "\n\n".join(
        doc.page_content for doc in docs
    )

    prompt = f"""
You are an intelligent PDF assistant.

Use ONLY the context below to answer.

If the user asks for a summary, summarize the available context.

If the answer cannot be found in the provided context, reply exactly:

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