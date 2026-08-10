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
# FASTAPI APP
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

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ============================================================
# GROQ LLM
# ============================================================

llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0
)


# ============================================================
# TAVILY
# ============================================================

tavily_api_key = os.getenv(
    "TAVILY_API_KEY"
)

tavily = None

if tavily_api_key:

    tavily = TavilyClient(
        api_key=tavily_api_key
    )

else:

    print(
        "WARNING: TAVILY_API_KEY not found."
    )


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
    # Safety: only use ONE PDF
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
                    e
                )

        pdf_files = [keep_file]

    # --------------------------------------------------------
    # No PDFs
    # --------------------------------------------------------

    if not pdf_files:

        vector_db = None

        if os.path.exists(FAISS_DIR):

            try:

                shutil.rmtree(
                    FAISS_DIR
                )

            except Exception as e:

                print(
                    "FAISS cleanup error:",
                    e
                )

        return {
            "documents": 0,
            "pages": 0,
            "chunks": 0
        }

    # --------------------------------------------------------
    # Read the single PDF
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

            if page_text:

                page_text = page_text.strip()

                if page_text:

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
            e
        )

        vector_db = None

        return {
            "documents": 1,
            "pages": 0,
            "chunks": 0
        }

    # --------------------------------------------------------
    # No extractable text
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
    # Split into chunks
    # --------------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
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
    # Create FAISS
    # --------------------------------------------------------

    vector_db = FAISS.from_documents(
        split_documents,
        embeddings
    )

    # --------------------------------------------------------
    # Save FAISS
    # --------------------------------------------------------

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
        "message": (
            "AI Knowledge Base Backend is Running 🚀"
        )
    }


# ============================================================
# UPLOAD ONE PDF
# ============================================================

@app.post("/upload")
async def upload_pdf(
    files: Annotated[
        list[UploadFile],
        File(description="One PDF file")
    ]
):

    global vector_db

    try:

        # ----------------------------------------------------
        # Validate upload
        # ----------------------------------------------------

        if not files:

            return {
                "message": "No PDF file was uploaded.",
                "files": [],
                "total_files": 0,
                "total_pages": 0,
                "chunks": 0,
                "document_stats": []
            }

        # ----------------------------------------------------
        # Use only the first file
        # ----------------------------------------------------

        file = files[0]

        if not file.filename:

            return {
                "message": "Invalid PDF file.",
                "files": [],
                "total_files": 0,
                "total_pages": 0,
                "chunks": 0,
                "document_stats": []
            }

        if not file.filename.lower().endswith(
            ".pdf"
        ):

            return {
                "message": "Only PDF files are allowed.",
                "files": [],
                "total_files": 0,
                "total_pages": 0,
                "chunks": 0,
                "document_stats": []
            }

        # ----------------------------------------------------
        # Remove previous PDFs
        # ----------------------------------------------------

        for old_filename in os.listdir(
            UPLOAD_DIR
        ):

            if not old_filename.lower().endswith(
                ".pdf"
            ):

                continue

            old_path = os.path.join(
                UPLOAD_DIR,
                old_filename
            )

            try:

                os.remove(
                    old_path
                )

                print(
                    "Removed previous PDF:",
                    old_filename
                )

            except Exception as e:

                print(
                    "Could not remove old PDF:",
                    old_filename,
                    e
                )

        # ----------------------------------------------------
        # Safe filename
        # ----------------------------------------------------

        safe_filename = os.path.basename(
            file.filename
        )

        file_path = os.path.join(
            UPLOAD_DIR,
            safe_filename
        )

        # ----------------------------------------------------
        # Save PDF
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
        # Rebuild RAG
        # ----------------------------------------------------

        stats = rebuild_vector_database()

        # ----------------------------------------------------
        # Document information
        # ----------------------------------------------------

        pages = 0
        chunks = 0

        try:

            reader = PdfReader(
                file_path
            )

            pages = len(
                reader.pages
            )

        except Exception as e:

            print(
                "Page count error:",
                e
            )

        if vector_db is not None:

            try:

                for doc in (
                    vector_db.docstore._dict.values()
                ):

                    if (
                        doc.metadata.get("source")
                        == safe_filename
                    ):

                        chunks += 1

            except Exception as e:

                print(
                    "Chunk count error:",
                    e
                )

        document_stats = [
            {
                "filename": safe_filename,
                "pages": pages,
                "chunks": chunks
            }
        ]

        # ----------------------------------------------------
        # Success response
        # ----------------------------------------------------

        return {
            "message": "PDF uploaded successfully",
            "files": [safe_filename],
            "total_files": 1,
            "total_pages": stats["pages"],
            "chunks": stats["chunks"],
            "document_stats": document_stats
        }

    except Exception as e:

        print(
            "Upload Error:",
            repr(e)
        )

        return {
            "message": "Upload failed",
            "error": str(e),
            "files": [],
            "total_files": 0,
            "total_pages": 0,
            "chunks": 0,
            "document_stats": []
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

        # Rebuild
        stats = rebuild_vector_database()

        return {
            "success": True,
            "message": (
                f"{safe_filename} deleted successfully."
            ),
            "total_files": stats["documents"],
            "total_pages": stats["pages"],
            "chunks": stats["chunks"]
        }

    except Exception as e:

        print(
            "Delete Error:",
            repr(e)
        )

        return {
            "success": False,
            "message": "Delete failed.",
            "error": str(e)
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
            "error": "Tavily API key is not configured."
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
            "error": str(e)
        }


# ============================================================
# QUESTION MODEL
# ============================================================

class Question(BaseModel):

    question: str

    use_web: bool = False

    # Kept for frontend compatibility.
    # The backend intentionally ignores multiple
    # document selection because this is single-PDF mode.
    selected_documents: list[str] = Field(
        default_factory=list
    )

    chat_history: list[dict] = Field(
        default_factory=list
    )


# ============================================================
# FORMAT CHAT HISTORY
# ============================================================

def format_chat_history(
    chat_history: list[dict]
):

    if not chat_history:

        return "No previous conversation."

    history_lines = []

    recent_history = chat_history[-10:]

    for message in recent_history:

        sender = message.get(
            "sender",
            "unknown"
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

    # Safety: use only the first PDF.
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
        "========================================"
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
        "Chat History Messages:",
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

    if current_pdf is None:

        return {
            "question": data.question,
            "answer": (
                "Please upload a PDF first."
            ),
            "sources": [],
            "web_sources": []
        }

    # ========================================================
    # CHECK VECTOR DATABASE
    # ========================================================

    if vector_db is None:

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

        if vector_db is None:

            return {
                "question": data.question,
                "answer": (
                    "The uploaded PDF could not be "
                    "processed. Please upload it again."
                ),
                "sources": [],
                "web_sources": []
            }

    # ========================================================
    # CHAT HISTORY
    # ========================================================

    chat_history_text = format_chat_history(
        data.chat_history
    )

    # ========================================================
    # RETRIEVAL QUERY
    # ========================================================

    retrieval_query = data.question

    # --------------------------------------------------------
    # Rewrite follow-up questions
    # --------------------------------------------------------

    if data.chat_history:

        rewrite_prompt = f"""
You are a query rewriting assistant for a PDF RAG system.

Rewrite the CURRENT QUESTION into a standalone search query.

Use the previous conversation only to understand references
such as:

it
this
that
they
the paper
the method
the approach
the model
the problem

Do NOT answer the question.

Return ONLY the rewritten search query.

PREVIOUS CONVERSATION:

{chat_history_text}

CURRENT QUESTION:

{data.question}

STANDALONE SEARCH QUERY:
"""

        try:

            rewrite_response = llm.invoke(
                rewrite_prompt
            )

            rewritten_query = (
                getattr(
                    rewrite_response,
                    "content",
                    ""
                )
                or ""
            )

            rewritten_query = (
                rewritten_query
                .strip()
                .replace(
                    "\n",
                    " "
                )
            )

            if rewritten_query:

                retrieval_query = rewritten_query

        except Exception as e:

            print(
                "Query rewrite error:",
                repr(e)
            )

            retrieval_query = data.question

    print(
        "Retrieval Query:",
        retrieval_query
    )

    # ========================================================
    # SEARCH QUERIES
    # ========================================================

    search_queries = [
        retrieval_query
    ]

    # --------------------------------------------------------
    # Query expansion
    # --------------------------------------------------------

    try:

        expansion_prompt = f"""
Create up to 3 alternative search queries for retrieving
information from a research paper.

Original question:

{retrieval_query}

Rules:

- Keep the same meaning.
- Use useful technical synonyms.
- Do not answer the question.
- Do not invent facts.
- Return ONLY queries.
- One query per line.
- Do not number them.
"""

        expansion_response = llm.invoke(
            expansion_prompt
        )

        expansion_text = (
            getattr(
                expansion_response,
                "content",
                ""
            )
            or ""
        )

        expanded_queries = []

        for line in expansion_text.splitlines():

            cleaned = line.strip()

            if not cleaned:

                continue

            if len(cleaned) >= 2:

                if (
                    cleaned[0].isdigit()
                    and cleaned[1] in [".", ")"]
                ):

                    cleaned = cleaned[2:].strip()

            if cleaned:

                expanded_queries.append(
                    cleaned
                )

        search_queries.extend(
            expanded_queries[:3]
        )

    except Exception as e:

        print(
            "Query expansion error:",
            repr(e)
        )

    search_queries = list(
        dict.fromkeys(
            search_queries
        )
    )

    print(
        "Search Queries:"
    )

    for query in search_queries:

        print(
            " -",
            query
        )

    # ========================================================
    # SINGLE-PDF RETRIEVAL
    # ========================================================

    document_results = []

    print(
        "Searching ONLY PDF:",
        current_pdf
    )

    for query in search_queries:

        try:

            results = (
                vector_db
                .similarity_search_with_score(
                    query,
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

                    document_results.append(
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

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique_results = {}

    for doc, score in document_results:

        key = (
            doc.metadata.get(
                "source"
            ),
            doc.metadata.get(
                "page"
            ),
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

    # ========================================================
    # SORT BY SCORE
    # ========================================================

    filtered_results.sort(
        key=lambda item: item[1]
    )

    # ========================================================
    # KEEP BEST 8 CHUNKS
    # ========================================================

    selected_results = (
        filtered_results[:8]
    )

    print(
        "Selected chunks:",
        len(selected_results)
    )

    for doc, score in selected_results:

        print(
            "Source:",
            doc.metadata.get(
                "source"
            ),
            "| Page:",
            doc.metadata.get(
                "page"
            ),
            "| Score:",
            score
        )

    # ========================================================
    # RELEVANCE CHECK
    # ========================================================

    RELEVANCE_THRESHOLD = 1.8

    docs = [
        doc
        for doc, score
        in selected_results
        if score <= RELEVANCE_THRESHOLD
    ]

    best_score = None

    if selected_results:

        best_score = min(
            score
            for doc, score
            in selected_results
        )

    print(
        "Best relevance score:",
        best_score
    )

    print(
        "Relevant chunks:",
        len(docs)
    )

    # ========================================================
    # FALLBACK
    # ========================================================

    # If the retrieval system found chunks but the threshold
    # rejected all of them, use the best chunks rather than
    # immediately refusing to answer.
    #
    # This prevents reasonable questions from failing because
    # of a small similarity-score difference.
    # ========================================================

    if not docs and selected_results:

        print(
            "No chunks passed threshold."
        )

        print(
            "Using best retrieved chunks as fallback."
        )

        docs = [
            doc
            for doc, score
            in selected_results[:5]
        ]

    # ========================================================
    # NO PDF CONTEXT
    # ========================================================

    if not docs:

        return {
            "question": data.question,
            "answer": (
                "The available PDF content does not contain "
                "enough information to answer this question."
            ),
            "sources": [],
            "web_sources": []
        }

    # ========================================================
    # BUILD PDF CONTEXT
    # ========================================================

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
            "pages": sorted(
                pages
            )
        }
        for source, pages
        in pdf_sources_map.items()
    ]

    # ========================================================
    # WEB VARIABLES
    # ========================================================

    web_context = ""

    web_sources = []

    # ========================================================
    # WEB SEARCH
    # ========================================================

    if data.use_web:

        if tavily is None:

            print(
                "Web Search requested but Tavily is not configured."
            )

        else:

            try:

                web_query_prompt = f"""
Create ONE concise web search query.

The user asks:

{data.question}

The uploaded PDF discusses:

{pdf_context[:6000]}

The query should:

1. Focus on the same subject as the PDF.
2. Focus on the user's current question.
3. Use important technical keywords.
4. Avoid unrelated topics.
5. Return ONLY the search query.
"""

                web_query_response = llm.invoke(
                    web_query_prompt
                )

                focused_query = (
                    getattr(
                        web_query_response,
                        "content",
                        ""
                    )
                    or ""
                )

                focused_query = (
                    focused_query
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

                results = tavily.search(
                    query=focused_query,
                    search_depth="advanced",
                    max_results=5
                )

                for item in results.get(
                    "results",
                    []
                ):

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
                        f"\nTitle: {title}\n"
                        f"Content: {content}\n"
                        f"URL: {url}\n\n"
                    )

            except Exception as e:

                print(
                    "Tavily Error:",
                    repr(e)
                )

    # ========================================================
    # FINAL PROMPT
    # ========================================================

    if data.use_web and web_context.strip():

        prompt = f"""
You are an AI Research Assistant.

The user has uploaded ONE PDF.

Answer the CURRENT QUESTION using:

1. The uploaded PDF as the primary source.
2. The relevant web search results.
3. Previous conversation ONLY to understand references.

IMPORTANT RULES:

- Do not invent facts.
- Do not use unrelated web information.
- Web information must be relevant to the PDF topic.
- Do not treat previous conversation as factual evidence.
- Clearly distinguish PDF information from web information.
- Stay directly related to the user's question.
- Give a detailed answer when the question asks for detail.

Use this structure:

## 📄 Information from the PDF

Give a detailed answer based on the PDF.

## 🌐 Additional Information from the Web

Give only relevant information from the web.

## 💡 Key Takeaways

- Important supported point
- Important supported point
- Important supported point

PREVIOUS CONVERSATION:

{chat_history_text}

PDF CONTEXT:

{pdf_context}

WEB CONTEXT:

{web_context}

CURRENT QUESTION:

{data.question}

ANSWER:
"""

    else:

        prompt = f"""
You are a strict PDF-based AI Research Assistant.

The user has uploaded ONE PDF.

Answer the CURRENT QUESTION using ONLY the PDF CONTEXT.

IMPORTANT RULES:

1. Use ONLY information supported by the PDF.
2. Do NOT use your own general knowledge.
3. Do NOT use information from the internet.
4. Do NOT guess.
5. Do NOT invent facts.
6. Previous conversation may ONLY be used to understand
   references such as "it", "this", "that", "they",
   "the method", or "the approach".
7. Previous conversation is NOT factual evidence.
8. Give a COMPLETE and DETAILED answer when the PDF
   contains enough information.
9. If the question asks for contributions, explain
   each contribution separately.
10. If the question asks for methodology, explain
    the methodology clearly and step by step.
11. If the question asks for findings or results,
    explain the findings supported by the PDF.
12. Do not make the answer short just because the
    question is simple.
13. Do not add facts merely to make the answer longer.
14. Every factual statement must be supported by
    the PDF CONTEXT.

If the PDF genuinely does not contain enough information,
respond ONLY with:

The available PDF content does not contain enough
information to answer this question.

Otherwise use:

## 📄 Detailed Answer

[Detailed answer based ONLY on the PDF.]

## 💡 Key Takeaways

- Supported point
- Supported point
- Supported point

PREVIOUS CONVERSATION:

{chat_history_text}

PDF CONTEXT:

{pdf_context}

CURRENT QUESTION:

{data.question}

ANSWER:
"""

    # ========================================================
    # GENERATE FINAL ANSWER
    # ========================================================

    print(
        "Generating final answer..."
    )

    try:

        response = llm.invoke(
            prompt
        )

        # ----------------------------------------------------
        # Protect against None
        # ----------------------------------------------------

        if response is None:

            print(
                "LLM returned None."
            )

            return {
                "question": data.question,
                "answer": (
                    "The AI model did not return an answer. "
                    "Please try again."
                ),
                "sources": pdf_sources,
                "web_sources": web_sources
            }

        # ----------------------------------------------------
        # Extract content
        # ----------------------------------------------------

        final_answer = getattr(
            response,
            "content",
            ""
        )

        if final_answer is None:

            final_answer = ""

        final_answer = str(
            final_answer
        ).strip()

        print(
            "Final answer length:",
            len(final_answer)
        )

        # ----------------------------------------------------
        # Empty response
        # ----------------------------------------------------

        if not final_answer:

            return {
                "question": data.question,
                "answer": (
                    "The AI model did not return an answer. "
                    "Please try again."
                ),
                "sources": pdf_sources,
                "web_sources": web_sources
            }

        # ----------------------------------------------------
        # Unsupported-answer detection
        # ----------------------------------------------------

        no_answer_phrases = [
            "the available pdf content does not contain enough information",
            "the answer could not be found in the uploaded documents",
            "does not contain enough information to answer"
        ]

        is_no_answer = any(
            phrase in final_answer.lower()
            for phrase in no_answer_phrases
        )

        if is_no_answer:

            return {
                "question": data.question,
                "answer": (
                    "The available PDF content does not contain "
                    "enough information to answer this question."
                ),
                "sources": [],
                "web_sources": []
            }

        # ====================================================
        # SUCCESS RESPONSE
        # ====================================================

        result = {
            "question": data.question,
            "answer": final_answer,
            "sources": pdf_sources,
            "web_sources": web_sources
        }

        print(
            "Returning answer successfully."
        )

        return result

    except Exception as e:

        print(
            "LLM Error:",
            repr(e)
        )

        return {
            "question": data.question,
            "answer": (
                "An error occurred while generating "
                "the answer. Please try again."
            ),
            "sources": pdf_sources,
            "web_sources": web_sources,
            "error": str(e)
        }


# ============================================================
# END
# ============================================================