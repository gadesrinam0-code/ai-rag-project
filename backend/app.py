import os
import shutil
from typing import Annotated

from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pydantic import BaseModel, Field
from pypdf import PdfReader

from tavily import TavilyClient


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI()


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
# DIRECTORIES
# ============================================================

UPLOAD_DIR = "uploads"
FAISS_DIR = "faiss_index"

os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# GROQ
# ============================================================

llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0
)


# ============================================================
# TAVILY
# ============================================================

tavily_api_key = os.getenv("TAVILY_API_KEY")

tavily = None

if tavily_api_key:
    tavily = TavilyClient(
        api_key=tavily_api_key
    )
else:
    print("WARNING: TAVILY_API_KEY not found.")


# ============================================================
# EMBEDDINGS
# ============================================================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# VECTOR DATABASE
# ============================================================

vector_db = None


# ============================================================
# REBUILD VECTOR DATABASE
# ============================================================

def rebuild_vector_database():

    global vector_db

    all_documents = []

    # --------------------------------------------------------
    # Find PDFs
    # --------------------------------------------------------

    pdf_files = [
        filename
        for filename in os.listdir(UPLOAD_DIR)
        if filename.lower().endswith(".pdf")
    ]

    # --------------------------------------------------------
    # SINGLE PDF MODE
    # --------------------------------------------------------

    if len(pdf_files) > 1:

        pdf_files.sort()

        keep_file = pdf_files[-1]

        print(
            "Multiple PDFs detected."
        )

        print(
            "Keeping only:",
            keep_file
        )

        for filename in pdf_files:

            if filename == keep_file:
                continue

            old_path = os.path.join(
                UPLOAD_DIR,
                filename
            )

            try:
                os.remove(old_path)

                print(
                    "Removed extra PDF:",
                    filename
                )

            except Exception as e:

                print(
                    "Could not remove:",
                    filename,
                    repr(e)
                )

        pdf_files = [keep_file]

    # --------------------------------------------------------
    # No PDF
    # --------------------------------------------------------

    if not pdf_files:

        vector_db = None

        if os.path.exists(FAISS_DIR):

            try:
                shutil.rmtree(FAISS_DIR)
            except Exception as e:
                print(
                    "FAISS cleanup error:",
                    repr(e)
                )

        return {
            "documents": 0,
            "pages": 0,
            "chunks": 0
        }

    # --------------------------------------------------------
    # Read PDF
    # --------------------------------------------------------

    filename = pdf_files[0]

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    print(
        "Building RAG for:",
        filename
    )

    try:

        reader = PdfReader(
            file_path
        )

        for page_number, page in enumerate(
            reader.pages
        ):

            page_text = page.extract_text()

            if not page_text:
                continue

            page_text = page_text.strip()

            if not page_text:
                continue

            all_documents.append(
                Document(
                    page_content=page_text,
                    metadata={
                        "source": filename,
                        "page": page_number + 1
                    }
                )
            )

    except Exception as e:

        print(
            "PDF reading error:",
            repr(e)
        )

        vector_db = None

        return {
            "documents": 1,
            "pages": 0,
            "chunks": 0
        }

    # --------------------------------------------------------
    # No text
    # --------------------------------------------------------

    if not all_documents:

        vector_db = None

        print(
            "No extractable text found in PDF."
        )

        return {
            "documents": 1,
            "pages": 0,
            "chunks": 0
        }

    # --------------------------------------------------------
    # Split
    # --------------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200
    )

    split_documents = splitter.split_documents(
        all_documents
    )

    print(
        "PDF pages:",
        len(all_documents)
    )

    print(
        "PDF chunks:",
        len(split_documents)
    )

    # --------------------------------------------------------
    # FAISS
    # --------------------------------------------------------

    vector_db = FAISS.from_documents(
        split_documents,
        embeddings
    )

    vector_db.save_local(
        FAISS_DIR
    )

    return {
        "documents": 1,
        "pages": len(all_documents),
        "chunks": len(split_documents)
    }


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_rebuild():

    try:

        stats = rebuild_vector_database()

        print(
            "Startup RAG rebuild complete:",
            stats
        )

    except Exception as e:

        print(
            "Startup RAG rebuild error:",
            repr(e)
        )


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message":
            "AI Knowledge Base Backend is Running 🚀"
    }


# ============================================================
# UPLOAD ONE PDF
# ============================================================

@app.post("/upload")
async def upload_pdf(
    files: Annotated[
        list[UploadFile],
        File(description="Upload one PDF")
    ]
):

    global vector_db

    try:

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        if not files:

            return {
                "message": "No PDF file was uploaded.",
                "files": [],
                "total_files": 0,
                "total_pages": 0,
                "chunks": 0
            }

        # ----------------------------------------------------
        # ONLY FIRST FILE
        # ----------------------------------------------------

        file = files[0]

        if not file.filename:

            return {
                "message": "Invalid PDF file.",
                "files": [],
                "total_files": 0,
                "total_pages": 0,
                "chunks": 0
            }

        if not file.filename.lower().endswith(".pdf"):

            return {
                "message": "Only PDF files are allowed.",
                "files": [],
                "total_files": 0,
                "total_pages": 0,
                "chunks": 0
            }

        # ----------------------------------------------------
        # DELETE ALL PREVIOUS PDFs
        # ----------------------------------------------------

        for old_filename in os.listdir(
            UPLOAD_DIR
        ):

            if not old_filename.lower().endswith(".pdf"):
                continue

            old_path = os.path.join(
                UPLOAD_DIR,
                old_filename
            )

            try:

                os.remove(old_path)

                print(
                    "Removed previous PDF:",
                    old_filename
                )

            except Exception as e:

                print(
                    "Could not remove old PDF:",
                    old_filename,
                    repr(e)
                )

        # ----------------------------------------------------
        # SAFE FILENAME
        # ----------------------------------------------------

        safe_filename = os.path.basename(
            file.filename
        )

        file_path = os.path.join(
            UPLOAD_DIR,
            safe_filename
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        print(
            "Uploaded single PDF:",
            safe_filename
        )

        # ----------------------------------------------------
        # REBUILD RAG
        # ----------------------------------------------------

        stats = rebuild_vector_database()

        return {
            "message":
                "PDF uploaded successfully",

            "files":
                [safe_filename],

            "total_files":
                1,

            "total_pages":
                stats["pages"],

            "chunks":
                stats["chunks"]
        }

    except Exception as e:

        print(
            "Upload Error:",
            repr(e)
        )

        return {
            "message":
                "Upload failed",

            "error":
                str(e)
        }


# ============================================================
# DELETE PDF
# ============================================================

@app.delete("/delete/{filename}")
def delete_document(
    filename: str
):

    global vector_db

    try:

        safe_filename = os.path.basename(
            filename
        )

        file_path = os.path.join(
            UPLOAD_DIR,
            safe_filename
        )

        if not os.path.exists(
            file_path
        ):

            return {
                "success": False,
                "message": "Document not found."
            }

        os.remove(
            file_path
        )

        print(
            "Deleted document:",
            safe_filename
        )

        stats = rebuild_vector_database()

        return {
            "success": True,
            "message":
                f"{safe_filename} deleted successfully.",
            "total_files":
                stats["documents"],
            "total_pages":
                stats["pages"],
            "chunks":
                stats["chunks"]
        }

    except Exception as e:

        print(
            "Delete Error:",
            repr(e)
        )

        return {
            "success": False,
            "message":
                "Delete failed.",
            "error":
                str(e)
        }


# ============================================================
# WEB SEARCH TEST
# ============================================================

@app.get("/websearch")
def web_search(
    query: str
):

    if tavily is None:

        return {
            "error":
                "Tavily API key is not configured."
        }

    try:

        result = tavily.search(
            query=query,
            search_depth="basic",
            max_results=3
        )

        return result

    except Exception as e:

        print(
            "Web Search Error:",
            repr(e)
        )

        return {
            "error":
                str(e)
        }


# ============================================================
# QUESTION MODEL
# ============================================================

class Question(BaseModel):

    question: str

    use_web: bool = False

    selected_documents: list[str] = Field(
        default_factory=list
    )

    chat_history: list[dict] = Field(
        default_factory=list
    )


# ============================================================
# CHAT HISTORY
# ============================================================

def format_chat_history(
    chat_history: list[dict]
):

    if not chat_history:

        return "No previous conversation."

    history_lines = []

    for message in chat_history[-10:]:

        sender = message.get(
            "sender",
            ""
        )

        text = message.get(
            "text",
            ""
        )

        if not text:
            continue

        if sender == "user":

            history_lines.append(
                f"User: {text}"
            )

        elif sender == "ai":

            history_lines.append(
                f"Assistant: {text}"
            )

    if not history_lines:

        return "No previous conversation."

    return "\n".join(
        history_lines
    )


# ============================================================
# GET CURRENT PDF
# ============================================================

def get_current_pdf():

    pdf_files = [
        filename
        for filename in os.listdir(
            UPLOAD_DIR
        )
        if filename.lower().endswith(".pdf")
    ]

    if not pdf_files:
        return None

    pdf_files.sort()

    return pdf_files[0]


# ============================================================
# ASK QUESTION
# ============================================================

@app.post("/ask")
async def ask_question(
    data: Question
):

    global vector_db

    print(
        "\n========================================"
    )

    print(
        "Question:",
        data.question
    )

    print(
        "Use Web:",
        data.use_web
    )

    print(
        "Chat History:",
        len(data.chat_history)
    )

    print(
        "========================================"
    )

    # ========================================================
    # CURRENT PDF
    # ========================================================

    current_pdf = get_current_pdf()

    print(
        "Current PDF:",
        current_pdf
    )

    # ========================================================
    # IMPORTANT:
    # WEB SEARCH CAN WORK WITHOUT PDF
    # ========================================================

    if current_pdf is None and not data.use_web:

        return {
            "question": data.question,
            "answer":
                "Please upload a PDF first.",
            "sources": [],
            "web_sources": []
        }

    # ========================================================
    # REBUILD PDF IF NECESSARY
    # ========================================================

    if current_pdf is not None and vector_db is None:

        try:

            stats = rebuild_vector_database()

            print(
                "Rebuilt vector database:",
                stats
            )

        except Exception as e:

            print(
                "RAG rebuild error:",
                repr(e)
            )

    # ========================================================
    # CHAT HISTORY
    # ========================================================

    chat_history_text = format_chat_history(
        data.chat_history
    )

    # ========================================================
    # PDF RETRIEVAL
    # ========================================================

    docs = []

    filtered_results = []

    if vector_db is not None and current_pdf:

        retrieval_query = data.question

        # ----------------------------------------------------
        # Rewrite follow-up question
        # ----------------------------------------------------

        if data.chat_history:

            rewrite_prompt = f"""
Rewrite the current user question into a
standalone search query for a research paper.

Use conversation only to resolve references
such as "it", "this", "that", "the paper",
"the method", or "the approach".

Do NOT answer the question.

Return ONLY the search query.

PREVIOUS CONVERSATION:

{chat_history_text}

CURRENT QUESTION:

{data.question}
"""

            try:

                rewrite_response = llm.invoke(
                    rewrite_prompt
                )

                rewritten = getattr(
                    rewrite_response,
                    "content",
                    ""
                )

                if rewritten:

                    rewritten = (
                        str(rewritten)
                        .strip()
                        .replace(
                            "\n",
                            " "
                        )
                    )

                    if rewritten:
                        retrieval_query = rewritten

            except Exception as e:

                print(
                    "Rewrite error:",
                    repr(e)
                )

        print(
            "Retrieval Query:",
            retrieval_query
        )

        # ----------------------------------------------------
        # Retrieval
        # ----------------------------------------------------

        try:

            results = (
                vector_db
                .similarity_search_with_score(
                    retrieval_query,
                    k=30
                )
            )

            for doc, score in results:

                source = doc.metadata.get(
                    "source",
                    ""
                )

                if (
                    source == current_pdf
                    or os.path.basename(source)
                    == current_pdf
                ):

                    filtered_results.append(
                        (
                            doc,
                            score
                        )
                    )

        except Exception as e:

            print(
                "Retrieval error:",
                repr(e)
            )

        # ----------------------------------------------------
        # Remove duplicates
        # ----------------------------------------------------

        unique_results = {}

        for doc, score in filtered_results:

            key = (
                doc.metadata.get("source"),
                doc.metadata.get("page"),
                doc.page_content[:300]
            )

            if (
                key not in unique_results
                or score < unique_results[key][1]
            ):

                unique_results[key] = (
                    doc,
                    score
                )

        filtered_results = list(
            unique_results.values()
        )

        filtered_results.sort(
            key=lambda item: item[1]
        )

        # ----------------------------------------------------
        # Best chunks
        # ----------------------------------------------------

        selected_results = (
            filtered_results[:8]
        )

        print(
            "Retrieved chunks:",
            len(selected_results)
        )

        for doc, score in selected_results:

            print(
                "Source:",
                doc.metadata.get("source"),
                "| Page:",
                doc.metadata.get("page"),
                "| Score:",
                score
            )

        # ----------------------------------------------------
        # Relevance
        # ----------------------------------------------------

        RELEVANCE_THRESHOLD = 1.8

        docs = [
            doc
            for doc, score in selected_results
            if score <= RELEVANCE_THRESHOLD
        ]

        # ----------------------------------------------------
        # Fallback
        # ----------------------------------------------------

        if not docs and selected_results:

            print(
                "No chunks passed threshold."
            )

            print(
                "Using best chunks as fallback."
            )

            docs = [
                doc
                for doc, score
                in selected_results[:5]
            ]

    print(
        "Relevant PDF chunks:",
        len(docs)
    )

    # ========================================================
    # PDF CONTEXT
    # ========================================================

    pdf_context = ""

    if docs:

        context_parts = []

        for doc in docs:

            source = doc.metadata.get(
                "source",
                current_pdf
            )

            page = doc.metadata.get(
                "page",
                "Unknown"
            )

            context_parts.append(
                f"[PDF: {source} | PAGE: {page}]\n"
                f"{doc.page_content}"
            )

        pdf_context = "\n\n".join(
            context_parts
        )

    print(
        "PDF context length:",
        len(pdf_context)
    )

    # ========================================================
    # PDF SOURCES
    # ========================================================

    pdf_sources_map = {}

    for doc in docs:

        source = doc.metadata.get(
            "source"
        )

        page = doc.metadata.get(
            "page"
        )

        if not source:
            continue

        if source not in pdf_sources_map:

            pdf_sources_map[source] = []

        if page not in pdf_sources_map[source]:

            pdf_sources_map[source].append(
                page
            )

    pdf_sources = [
        {
            "source": source,
            "pages": sorted(pages)
        }
        for source, pages
        in pdf_sources_map.items()
    ]

    # ========================================================
    # WEB SEARCH VARIABLES
    # ========================================================

    web_context = ""

    web_sources = []

    # ========================================================
    # WEB SEARCH
    # ========================================================

    if data.use_web:

        print(
            "WEB SEARCH ENABLED"
        )

        if tavily is None:

            print(
                "Tavily is not configured."
            )

        else:

            try:

                # ------------------------------------------------
                # Build web query
                # ------------------------------------------------

                web_query_prompt = f"""
Create ONE concise web search query.

The user asks:

{data.question}

Current year: 2026.

Previous conversation:

{chat_history_text}

PDF context, if available:

{pdf_context[:5000]}

Rules:

1. Focus on the user's current question.
2. If the user asks for latest/current/recent information,
   search for current information.
3. If the question refers to the PDF, keep the same topic.
4. Include important technical keywords.
5. Do not answer the question.
6. Return ONLY the search query.
"""

                query_response = llm.invoke(
                    web_query_prompt
                )

                focused_query = getattr(
                    query_response,
                    "content",
                    ""
                )

                focused_query = (
                    str(focused_query or "")
                    .strip()
                    .replace(
                        "\n",
                        " "
                    )
                    .strip(
                        "\"'"
                    )
                )

                if not focused_query:

                    focused_query = data.question

                print(
                    "Focused Web Query:",
                    focused_query
                )

                # ------------------------------------------------
                # Tavily
                # ------------------------------------------------

                results = tavily.search(
                    query=focused_query,
                    search_depth="advanced",
                    max_results=5
                )

                web_items = results.get(
                    "results",
                    []
                )

                print(
                    "Web results:",
                    len(web_items)
                )

                for item in web_items:

                    title = item.get(
                        "title",
                        "Web Source"
                    )

                    url = item.get(
                        "url",
                        ""
                    )

                    content = item.get(
                        "content",
                        ""
                    )

                    if url:

                        web_sources.append(
                            {
                                "title": title,
                                "url": url
                            }
                        )

                    web_context += (
                        f"\n"
                        f"Title: {title}\n"
                        f"Content: {content}\n"
                        f"URL: {url}\n"
                    )

            except Exception as e:

                print(
                    "Tavily Error:",
                    repr(e)
                )

    # ========================================================
    # NO PDF + NO WEB
    # ========================================================

    if not docs and not data.use_web:

        return {
            "question": data.question,
            "answer":
                "The available PDF content does not contain "
                "enough information to answer this question.",
            "sources": [],
            "web_sources": []
        }

    # ========================================================
    # NO PDF BUT WEB IS AVAILABLE
    # ========================================================

    if data.use_web and web_context.strip():

        prompt = f"""
You are an AI Research Assistant.

The user has uploaded ONE PDF.

Web Search is ENABLED.

Answer the CURRENT QUESTION using:

1. PDF information when relevant.
2. Web Search information when the PDF does not contain
   enough information.
3. Previous conversation only to understand references.

IMPORTANT:

- Do NOT invent facts.
- Do NOT use unrelated information.
- Current/latest questions should use the web results.
- If the PDF does not contain the answer, use the web.
- Clearly distinguish PDF information and web information.
- Give a detailed answer.
- Do not refuse merely because the PDF does not contain
  the answer.

Use EXACTLY this structure:

## 📄 Information from the PDF

Explain the relevant information from the uploaded PDF.

If the PDF does not contain relevant information,
write:

The PDF does not contain enough information about
this specific question.

## 🌐 Additional Information from the Web

Explain the relevant information found through Web Search.

## 💡 Key Takeaways

- Important point
- Important point
- Important point

PREVIOUS CONVERSATION:

{chat_history_text}

PDF CONTEXT:

{pdf_context}

WEB SEARCH CONTEXT:

{web_context}

CURRENT QUESTION:

{data.question}

ANSWER:
"""

    elif data.use_web:

        prompt = f"""
You are an AI Research Assistant.

Web Search was requested, but no useful web results
were retrieved.

Answer using the uploaded PDF if possible.

If the PDF does not contain enough information, say so.

Do NOT invent facts.

Use this structure:

## 📄 Information from the PDF

[Relevant PDF information]

## 🌐 Additional Information from the Web

No relevant web information was retrieved.

## 💡 Key Takeaways

- Important supported point
- Important supported point

PDF CONTEXT:

{pdf_context}

CURRENT QUESTION:

{data.question}

ANSWER:
"""

    else:

        prompt = f"""
You are a strict PDF Research Assistant.

Answer the user's question using ONLY the uploaded PDF.

Do NOT use outside knowledge.

Do NOT invent facts.

Previous conversation can ONLY be used to
understand references.

Give a detailed answer.

If the PDF contains enough information, use:

## 📄 Detailed Answer

[Detailed answer]

## 💡 Key Takeaways

- Important point
- Important point
- Important point

If the PDF genuinely does not contain enough
information, say:

The available PDF content does not contain enough
information to answer this question.

PREVIOUS CONVERSATION:

{chat_history_text}

PDF CONTEXT:

{pdf_context}

CURRENT QUESTION:

{data.question}

ANSWER:
"""

    # ========================================================
    # GENERATE ANSWER
    # ========================================================

    print(
        "Generating final answer..."
    )

    try:

        response = llm.invoke(
            prompt
        )

        if response is None:

            return {
                "question": data.question,
                "answer":
                    "The AI model did not return an answer. "
                    "Please try again.",
                "sources": pdf_sources,
                "web_sources": web_sources
            }

        final_answer = getattr(
            response,
            "content",
            ""
        )

        final_answer = str(
            final_answer or ""
        ).strip()

        print(
            "Final answer length:",
            len(final_answer)
        )

        if not final_answer:

            return {
                "question": data.question,
                "answer":
                    "The AI model did not return an answer. "
                    "Please try again.",
                "sources": pdf_sources,
                "web_sources": web_sources
            }

        # ====================================================
        # NO ANSWER CHECK
        # ====================================================

        no_answer_phrases = [
            "the available pdf content does not contain enough information",
            "does not contain enough information to answer",
            "the answer could not be found in the uploaded documents"
        ]

        answer_lower = final_answer.lower()

        is_no_answer = any(
            phrase in answer_lower
            for phrase in no_answer_phrases
        )

        # ----------------------------------------------------
        # WEB SEARCH HAS RESULTS
        # ----------------------------------------------------

        if (
            is_no_answer
            and data.use_web
            and web_context.strip()
        ):

            print(
                "PDF insufficient, but web context exists."
            )

            # Do NOT reject the answer.
            # The web is allowed to provide the answer.

        # ----------------------------------------------------
        # PDF ONLY
        # ----------------------------------------------------

        elif (
            is_no_answer
            and not data.use_web
        ):

            final_answer = (
                "The available PDF content does not contain "
                "enough information to answer this question."
            )

            pdf_sources = []

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return {
            "question": data.question,
            "answer": final_answer,
            "sources": pdf_sources,
            "web_sources": web_sources
        }

    except Exception as e:

        print(
            "LLM Error:",
            repr(e)
        )

        return {
            "question": data.question,
            "answer":
                "An error occurred while generating "
                "the answer. Please try again.",
            "sources": pdf_sources,
            "web_sources": web_sources,
            "error": str(e)
        }


# ============================================================
# END
# ============================================================