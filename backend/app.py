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
from tavily import TavilyClient

# Load environment variables
load_dotenv()

app = FastAPI()

# Groq LLM
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0
)

# Tavily Client
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Embedding model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Vector DB
vector_db = None

# CORS
app.add_middleware(
    CORSMiddleware,
      allow_origins=[
        "http://localhost:5173",
        "https://ai-rag-project-psi.vercel.app",

        "https://ai-rag-project-opdye221x-gadesrinam0-3714s-projects.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        file_path = os.path.join("uploads", file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )

        chunks = splitter.split_text(text)

        vector_db = FAISS.from_texts(
            chunks,
            embeddings
        )

        vector_db.save_local("faiss_index")

        return {
            "message": "PDF uploaded successfully",
            "filename": file.filename,
            "characters": len(text),
            "chunks": len(chunks),
        }

    except Exception as e:
        return {
            "message": "Upload failed",
            "error": str(e)
        }


# Test Tavily
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


class Question(BaseModel):
    question: str
    use_web: bool = False


@app.post("/ask")
async def ask_question(data: Question):
    print("Question:", data.question)
    print("Use Web:", data.use_web)

    global vector_db

    if vector_db is None:
        return {
            "answer": "Please upload a PDF first."
        }

    # ------------------------
    # Search PDF
    # ------------------------

    docs = vector_db.similarity_search(
        data.question,
        k=5
    )

    pdf_context = "\n\n".join(
        doc.page_content for doc in docs
    )

    # ------------------------
    # Search Web (only if enabled)
    # ------------------------

    web_context = ""

    if data.use_web:
        try:
            # Use a simple, focused search query
            search_query = f"{data.question} latest research 2025 2026"

            print("Search Query:", search_query)

            results = tavily.search(
                query=search_query,
                search_depth="advanced",
                max_results=8
            )

            print("Tavily Results:",results)

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
            print("Tavily Error:", e)

    # ------------------------
    # Prompt
    # ------------------------

    prompt = f"""
You are an AI Research Assistant.

Your task is to answer questions using the uploaded PDF and, when available,
web search results.

Instructions:

1. First answer using the uploaded PDF.
2. If Web Context is available, provide ONLY additional information that is NOT already present in the PDF.
3. Include:
   - recent developments
   - latest techniques
   - examples
   - best practices
   - real-world applications
4. Do NOT repeat information from the PDF.
5. If no useful web information exists, say:
   "No additional relevant information was found from web sources."

Format your answer like this:

## 📄 Information from the PDF
...

## 🌐 Additional Information from the Web
...

## 💡 Key Takeaways
...

==========================
PDF Context
==========================

{pdf_context}

==========================
Web Context
==========================

{web_context}

==========================

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
        return {
            "error": str(e)
        }