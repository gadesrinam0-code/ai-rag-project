import os
import shutil
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pydantic import BaseModel
from pypdf import PdfReader
from tavily import TavilyClient


# ============================================================
# Load environment variables
# ============================================================

load_dotenv()


# ============================================================
# FastAPI App
# ============================================================

app = FastAPI()


# ============================================================
# Groq LLM
# ============================================================

llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0
)


# ============================================================
# Tavily Client
# ============================================================

tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


# ============================================================
# Embedding Model
# ============================================================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# Vector Database
# ============================================================

vector_db = None


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Create required folders
# ============================================================

os.makedirs("uploads", exist_ok=True)


# ============================================================
# Home Route
# ============================================================

@app.get("/")
def home():
    return {
        "message": "AI Knowledge Base Backend is Running 🚀"
    }


# ============================================================
# MULTI-PDF UPLOAD
# ============================================================

@app.post("/upload")
async def upload_pdf(files: List[UploadFile] = File(...)):
    global vector_db

    try:
        all_documents = []
        uploaded_files = []

        # --------------------------------------------------------
        # Process every uploaded PDF
        # --------------------------------------------------------

        for file in files:

            # Check file type
            if not file.filename.lower().endswith(".pdf"):
                continue

            # Save PDF
            file_path = os.path.join(
                "uploads",
                file.filename
            )

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(
                    file.file,
                    buffer
                )

            uploaded_files.append(file.filename)

            # ----------------------------------------------------
            # Read PDF
            # ----------------------------------------------------

            reader = PdfReader(file_path)

            # ----------------------------------------------------
            # Extract text page by page
            # ----------------------------------------------------

            for page_number, page in enumerate(reader.pages):

                page_text = page.extract_text()

                if page_text:

                    all_documents.append(
                        Document(
                            page_content=page_text,
                            metadata={
                                "source": file.filename,
                                "page": page_number + 1
                            }
                        )
                    )

        # --------------------------------------------------------
        # Check whether PDFs were uploaded
        # --------------------------------------------------------

        if not all_documents:

            return {
                "message": "No readable PDF files were uploaded."
            }

        # --------------------------------------------------------
        # Split documents into chunks
        # --------------------------------------------------------

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )

        split_documents = splitter.split_documents(
            all_documents
        )

        # --------------------------------------------------------
        # Create FAISS vector database
        # --------------------------------------------------------

        vector_db = FAISS.from_documents(
            split_documents,
            embeddings
        )

        # --------------------------------------------------------
        # Save FAISS index
        # --------------------------------------------------------

        vector_db.save_local(
            "faiss_index"
        )

        # --------------------------------------------------------
        # Response
        # --------------------------------------------------------

        return {
            "message": "PDFs uploaded successfully",
            "files": uploaded_files,
            "total_files": len(uploaded_files),
            "total_pages": len(all_documents),
            "chunks": len(split_documents)
        }

    except Exception as e:

        print("Upload Error:", e)

        return {
            "message": "Upload failed",
            "error": str(e)
        }


# ============================================================
# WEB SEARCH TEST ROUTE
# ============================================================

@app.get("/websearch")
def web_search(query: str):

    try:

        result = tavily.search(
            query=query,
            search_depth="basic",
            max_results=3
        )

        return result

    except Exception as e:

        return {
            "error": str(e)
        }


# ============================================================
# Question Model
# ============================================================

class Question(BaseModel):

    question: str

    use_web: bool = False


# ============================================================
# ASK QUESTION
# ============================================================

@app.post("/ask")
async def ask_question(data: Question):

    print("Question:", data.question)

    print("Use Web:", data.use_web)

    global vector_db

    # --------------------------------------------------------
    # Check whether PDF knowledge base exists
    # --------------------------------------------------------

    if vector_db is None:

        return {
            "answer": "Please upload a PDF first."
        }

    # ========================================================
    # SEARCH PDF
    # ========================================================

    docs = vector_db.similarity_search(
        data.question,
        k=5
    )

    # --------------------------------------------------------
    # Create PDF context
    # --------------------------------------------------------

    pdf_context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    # ========================================================
    # WEB SEARCH
    # ========================================================

    web_context = ""

    if data.use_web:

        try:

            search_query = (
                f"{data.question} "
                "latest research 2025 2026"
            )

            print(
                "Search Query:",
                search_query
            )

            results = tavily.search(
                query=search_query,
                search_depth="advanced",
                max_results=8
            )

            print(
                "Tavily Results:",
                results
            )

            for item in results["results"]:

                web_context += f"""
Title:
{item['title']}

Content:
{item['content']}

URL:
{item['url']}

"""

        except Exception as e:

            print(
                "Tavily Error:",
                e
            )

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
You are an AI Research Assistant.

Your task is to answer questions using the uploaded PDFs
and, when available, web search results.

Instructions:

1. First answer using the uploaded PDF information.

2. If Web Context is available, provide ONLY additional
information that is NOT already present in the PDF.

3. Include:
   - recent developments
   - latest techniques
   - examples
   - best practices
   - real-world applications

4. Do NOT unnecessarily repeat information from the PDF.

5. If no useful web information exists, say:

"No additional relevant information was found from web sources."

Format your answer like this:

## 📄 Information from the PDF

...

## 🌐 Additional Information from the Web

...

## 💡 Key Takeaways

...

============================================================
PDF Context
============================================================

{pdf_context}

============================================================
Web Context
============================================================

{web_context}

============================================================

Question:

{data.question}

Answer:
"""

    # ========================================================
    # GENERATE ANSWER
    # ========================================================

    try:

        response = llm.invoke(
            prompt
        )

        return {
            "question": data.question,
            "answer": response.content
        }

    except Exception as e:

        print(
            "LLM Error:",
            e
        )

        return {
            "error": str(e)
        }