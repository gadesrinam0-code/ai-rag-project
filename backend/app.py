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
# GROQ LLM
# ============================================================

llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0
)


# ============================================================
# TAVILY
# ============================================================

tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
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
# UPLOAD DIRECTORY
# ============================================================

os.makedirs("uploads", exist_ok=True)


# ============================================================
# REBUILD VECTOR DATABASE
# ============================================================

def rebuild_vector_database():

    global vector_db

    all_documents = []

    for filename in os.listdir("uploads"):

        if not filename.lower().endswith(".pdf"):
            continue

        file_path = os.path.join(
            "uploads",
            filename
        )

        try:

            reader = PdfReader(file_path)

            for page_number, page in enumerate(
                reader.pages
            ):

                page_text = page.extract_text()

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
                f"Error reading {filename}:",
                e
            )

    # ========================================================
    # NO DOCUMENTS
    # ========================================================

    if not all_documents:

        vector_db = None

        if os.path.exists("faiss_index"):

            shutil.rmtree("faiss_index")

        return {
            "documents": 0,
            "pages": 0,
            "chunks": 0
        }

    # ========================================================
    # SPLIT DOCUMENTS
    # ========================================================

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )

    split_documents = splitter.split_documents(
        all_documents
    )

    # ========================================================
    # CREATE FAISS
    # ========================================================

    vector_db = FAISS.from_documents(
        split_documents,
        embeddings
    )

    # ========================================================
    # SAVE FAISS
    # ========================================================

    vector_db.save_local(
        "faiss_index"
    )

    return {
        "documents": len(
            set(
                doc.metadata.get("source")
                for doc in all_documents
            )
        ),
        "pages": len(all_documents),
        "chunks": len(split_documents)
    }


# ============================================================
# STARTUP REBUILD
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
            e
        )


# ============================================================
# HOME
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
async def upload_pdf(
    files: Annotated[
        list[UploadFile],
        File(description="Multiple PDF files")
    ]
):

    try:

        uploaded_files = []

        for file in files:

            if not file.filename.lower().endswith(".pdf"):
                continue

            file_path = os.path.join(
                "uploads",
                file.filename
            )

            with open(
                file_path,
                "wb"
            ) as buffer:

                shutil.copyfileobj(
                    file.file,
                    buffer
                )

            uploaded_files.append(
                file.filename
            )

        # ====================================================
        # REBUILD
        # ====================================================

        stats = rebuild_vector_database()

        # ====================================================
        # DOCUMENT STATS
        # ====================================================

        document_stats = []

        for filename in sorted(
            os.listdir("uploads")
        ):

            if not filename.lower().endswith(".pdf"):
                continue

            file_path = os.path.join(
                "uploads",
                filename
            )

            try:

                reader = PdfReader(
                    file_path
                )

                pages = len(
                    reader.pages
                )

                document_chunks = 0

                if vector_db is not None:

                    for doc in vector_db.docstore._dict.values():

                        if (
                            doc.metadata.get("source")
                            == filename
                        ):

                            document_chunks += 1

                document_stats.append(
                    {
                        "filename": filename,
                        "pages": pages,
                        "chunks": document_chunks
                    }
                )

            except Exception as e:

                print(
                    f"Stats error for {filename}:",
                    e
                )

        return {
            "message": "PDFs uploaded successfully",
            "files": uploaded_files,
            "total_files": stats["documents"],
            "total_pages": stats["pages"],
            "chunks": stats["chunks"],
            "document_stats": document_stats
        }

    except Exception as e:

        print(
            "Upload Error:",
            e
        )

        return {
            "message": "Upload failed",
            "error": str(e)
        }


# ============================================================
# DELETE DOCUMENT
# ============================================================

@app.delete("/delete/{filename}")
def delete_document(
    filename: str
):

    try:

        safe_filename = os.path.basename(
            filename
        )

        file_path = os.path.join(
            "uploads",
            safe_filename
        )

        if not os.path.exists(file_path):

            return {
                "success": False,
                "message": "Document not found."
            }

        os.remove(file_path)

        print(
            "Deleted document:",
            safe_filename
        )

        # ====================================================
        # REBUILD FAISS
        # ====================================================

        stats = rebuild_vector_database()

        # ====================================================
        # UPDATED DOCUMENT STATS
        # ====================================================

        document_stats = []

        for filename_item in sorted(
            os.listdir("uploads")
        ):

            if not filename_item.lower().endswith(".pdf"):
                continue

            current_path = os.path.join(
                "uploads",
                filename_item
            )

            try:

                reader = PdfReader(
                    current_path
                )

                pages = len(
                    reader.pages
                )

                chunks = 0

                if vector_db is not None:

                    for doc in vector_db.docstore._dict.values():

                        if (
                            doc.metadata.get("source")
                            == filename_item
                        ):

                            chunks += 1

                document_stats.append(
                    {
                        "filename": filename_item,
                        "pages": pages,
                        "chunks": chunks
                    }
                )

            except Exception as e:

                print(
                    "Document stats error:",
                    e
                )

        return {
            "success": True,
            "message": (
                f"{safe_filename} deleted successfully."
            ),
            "total_files": stats["documents"],
            "total_pages": stats["pages"],
            "chunks": stats["chunks"],
            "document_stats": document_stats
        }

    except Exception as e:

        print(
            "Delete Error:",
            e
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
# QUESTION MODEL
# ============================================================

class Question(BaseModel):

    question: str

    use_web: bool = False

    selected_documents: list[str] = Field(
        default_factory=list
    )

    # ========================================================
    # DAY 5 — CONVERSATION MEMORY
    # ========================================================

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

    # Keep the most recent 10 messages
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
# ASK QUESTION
# ============================================================

@app.post("/ask")
async def ask_question(
    data: Question
):

    global vector_db

    print(
        "Question:",
        data.question
    )

    print(
        "Use Web:",
        data.use_web
    )

    print(
        "Selected Documents:",
        data.selected_documents
    )

    print(
        "Chat History Messages:",
        len(data.chat_history)
    )

    # ========================================================
    # FORMAT CONVERSATION HISTORY
    # ========================================================

    chat_history_text = format_chat_history(
        data.chat_history
    )

    print(
        "Conversation history received."
    )

    # ========================================================
    # CHECK VECTOR DATABASE
    # ========================================================

    if vector_db is None:

        return {
            "answer": "Please upload a PDF first.",
            "sources": [],
            "web_sources": []
        }

    # ========================================================
    # QUERY FOR RETRIEVAL
    #
    # Use the current question for normal questions.
    # For follow-up questions, rewrite it using the
    # conversation history so retrieval understands
    # references such as "it", "this", "that method", etc.
    # ========================================================

    retrieval_query = data.question

    if data.chat_history:

        rewrite_prompt = f"""
You are a query rewriting assistant for a PDF RAG system.

Your job is to rewrite the user's CURRENT QUESTION
into a standalone search query.

Use the previous conversation only to resolve references
such as:

- it
- they
- this
- that
- this method
- the approach
- the paper
- the model
- the problem

Do NOT answer the question.

Return ONLY the rewritten search query.

============================================================
PREVIOUS CONVERSATION
============================================================

{chat_history_text}

============================================================
CURRENT QUESTION
============================================================

{data.question}

============================================================
STANDALONE SEARCH QUERY
============================================================
"""

        try:

            rewrite_response = llm.invoke(
                rewrite_prompt
            )

            rewritten_query = (
                rewrite_response.content
                .strip()
                .replace("\n", " ")
            )

            if rewritten_query:

                retrieval_query = rewritten_query

            print(
                "Retrieval Query:",
                retrieval_query
            )

        except Exception as e:

            print(
                "Query rewrite error:",
                e
            )

            retrieval_query = data.question

    # ========================================================
    # DAY 5 — STEP 2
    # BETTER DOCUMENT SEARCH / QUERY EXPANSION
    # ========================================================

    search_queries = [
        retrieval_query
    ]

    # --------------------------------------------------------
    # Generate alternative search queries
    # --------------------------------------------------------

    try:

        expansion_prompt = f"""
You are a search-query expansion assistant for a PDF RAG system.

Create up to 3 alternative search queries that can help
retrieve relevant passages from a research paper.

Rules:

1. Keep the same meaning as the original query.
2. Use useful technical synonyms.
3. Include important concepts from the question.
4. Do NOT answer the question.
5. Do NOT invent facts.
6. Return ONLY the alternative queries.
7. Put each query on a separate line.
8. Do not number the queries.

Original query:

{retrieval_query}
"""

        expansion_response = llm.invoke(
            expansion_prompt
        )

        expanded_queries = [
            line.strip()
            for line in expansion_response.content.splitlines()
            if line.strip()
        ]

        cleaned_queries = []

        for query in expanded_queries:

            cleaned = query.strip()

            if len(cleaned) >= 2:

                if (
                    cleaned[0].isdigit()
                    and cleaned[1] in [".", ")"]
                ):

                    cleaned = cleaned[2:].strip()

            if cleaned:

                cleaned_queries.append(
                    cleaned
                )

        search_queries.extend(
            cleaned_queries[:3]
        )

    except Exception as e:

        print(
            "Query expansion error:",
            e
        )

    # --------------------------------------------------------
    # Remove duplicate queries
    # --------------------------------------------------------

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
    # DAY 5 — STEP 3
    # BALANCED MULTI-PDF RETRIEVAL
    # ========================================================

    available_documents = [
        filename
        for filename in os.listdir("uploads")
        if filename.lower().endswith(".pdf")
    ]

    if data.selected_documents:
        documents_to_search = [
            filename
            for filename in available_documents
            if filename in data.selected_documents
        ]
    else:
        documents_to_search = available_documents

    print(
        "Documents used for comparison:",
        documents_to_search
    )

    # Search each PDF separately so one PDF cannot crowd
    # the other PDF out of the top results.
    all_retrieved_results = []

    for document_name in documents_to_search:

        print(
            "Searching PDF:",
            document_name
        )

        document_results = []

        for query in search_queries:

            try:

                results = (
                    vector_db.similarity_search_with_score(
                        query,
                        k=30
                    )
                )

                for doc, score in results:
                    source = doc.metadata.get("source", "")

                    if (
                         source == document_name
                         or os.path.basename(source) == document_name
                    ):

                        document_results.append(
                            (doc, score)
                        )

            except Exception as e:

                print(
                    "Retrieval error for",
                    document_name,
                    ":",
                    e
                )

        # Remove duplicate chunks within this PDF.
        unique_document_results = {}

        for doc, score in document_results:

            chunk_key = (
                doc.metadata.get("source"),
                doc.metadata.get("page"),
                doc.page_content[:200]
            )

            if (
                chunk_key not in unique_document_results
                or score < unique_document_results[chunk_key][1]
            ):

                unique_document_results[chunk_key] = (
                    doc,
                    score
                )

        document_results = list(
            unique_document_results.values()
        )

        document_results.sort(
            key=lambda item: item[1]
        )

        # Keep up to 4 relevant chunks from THIS PDF.
        selected_for_document = document_results[:4]

        print(
            "Selected chunks from",
            document_name,
            ":",
            len(selected_for_document)
        )

        for doc, score in selected_for_document:

            print(
                "  Source:",
                doc.metadata.get("source"),
                "| Page:",
                doc.metadata.get("page"),
                "| Score:",
                score
            )

        all_retrieved_results.extend(
            selected_for_document
        )

    filtered_results = all_retrieved_results

    filtered_results.sort(
        key=lambda item: item[1]
    )

    print(
        "Total multi-PDF retrieved chunks:",
        len(filtered_results)
    )

    # ========================================================
    # REMOVE DUPLICATE CHUNKS
    # ========================================================

    unique_results = {}

    for doc, score in filtered_results:

        chunk_key = (
            doc.metadata.get("source"),
            doc.metadata.get("page"),
            doc.page_content[:200]
        )

        if (
            chunk_key not in unique_results
            or score < unique_results[chunk_key][1]
        ):

            unique_results[chunk_key] = (
                doc,
                score
            )

    filtered_results = list(
        unique_results.values()
    )

    # ========================================================
    # SORT BY BEST SIMILARITY
    # ========================================================

    filtered_results.sort(
        key=lambda item: item[1]
    )

    # ========================================================
    # DEBUG RETRIEVAL
    # ========================================================

    print(
        "Total unique retrieved chunks:",
        len(filtered_results)
    )

    for doc, score in filtered_results[:10]:

        print(
            "Source:",
            doc.metadata.get("source"),
            "| Page:",
            doc.metadata.get("page"),
            "| Score:",
            score
        )

    # ========================================================
    # RELEVANCE CHECK
    # ========================================================

    RELEVANCE_THRESHOLD = 1.8

    if not filtered_results:

        best_score = None
        docs = []

    else:

        best_score = min(
            score
            for doc, score in filtered_results
        )

        docs = [
            doc
            for doc, score in filtered_results
            if score <= RELEVANCE_THRESHOLD
        ]

        print(
            "Best relevance score:",
            best_score
        )

        print(
            "Relevant chunks:",
            len(docs)
        )

    # ========================================================
    # DEBUG RETRIEVAL
    # ========================================================

    print(
        "Retrieved chunks:",
        len(docs)
    )

    for doc, score in filtered_results[:5]:

        print(
            "Source:",
            doc.metadata.get("source"),
            "| Page:",
            doc.metadata.get("page"),
            "| Score:",
            score
        )

    # ========================================================
    # NO RELEVANT PDF INFORMATION
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
    # PDF CONTEXT
    # ========================================================

    # Include source and page labels so the LLM can keep
    # information from different PDFs separate.
    context_parts = []

    for doc in docs:

        source = doc.metadata.get(
            "source",
            "Unknown PDF"
        )

        page = doc.metadata.get(
            "page",
            "Unknown"
        )

        context_parts.append(
            f"[SOURCE: {source} | PAGE: {page}]\n"
            f"{doc.page_content}"
        )

    pdf_context = "\n\n".join(
        context_parts
    )

    # ========================================================
    # PDF SOURCES
    # ========================================================

    pdf_sources = {}

    for doc in docs:

        source = doc.metadata.get(
            "source"
        )

        page = doc.metadata.get(
            "page"
        )

        if source:

            if source not in pdf_sources:

                pdf_sources[source] = []

            if page not in pdf_sources[source]:

                pdf_sources[source].append(
                    page
                )

    pdf_sources = [
        {
            "source": source,
            "pages": sorted(pages)
        }
        for source, pages
        in pdf_sources.items()
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

        try:

            search_prompt = f"""
You are helping an AI research assistant perform
a focused web search.

The user asked:

{data.question}

The previous conversation was:

{chat_history_text}

Here is information retrieved from the uploaded PDF:

{pdf_context[:6000]}

Create ONE concise web search query.

The query must:

1. Focus on the SAME subject discussed in the PDF.
2. Resolve references using the conversation if necessary.
3. Include the important technical/topic keywords.
4. Reflect the user's current question.
5. Avoid unrelated political, economic, climate,
   medical, or general news topics unless directly
   relevant to the PDF.
6. Be suitable for a search engine.
7. Return ONLY the search query.
8. Do not explain your answer.
"""

            query_response = llm.invoke(
                search_prompt
            )

            focused_query = (
                query_response.content
                .strip()
                .replace("\n", " ")
            )

            focused_query = focused_query.strip(
                "\"'"
            )

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

                web_context += f"""

Title:
{title}

Content:
{content}

URL:
{url}

"""

        except Exception as e:

            print(
                "Tavily Error:",
                e
            )

    # ========================================================
    # WEB SEARCH ON
    # ========================================================

    if data.use_web and web_context.strip():

        prompt = f"""
You are an AI Research Assistant.

Answer the user's CURRENT question using:

1. The uploaded PDF.
2. The relevant web search results.
3. The previous conversation ONLY when needed to
   understand references.

IMPORTANT RULES:

1. The uploaded PDF is the primary source.

2. Web information must be directly relevant to
   the SAME topic as the PDF and the user's question.

3. Do NOT use unrelated web information.

4. Do NOT invent information.

5. Do NOT claim something came from the web unless
   supported by the Web Context.

6. Use conversation history to understand references,
   but do not treat previous answers as evidence.

7. If the PDF and web results do not contain enough
   information, say so rather than guessing.

Format:

## 📄 Information from the PDF

[Answer based on the PDF]

## 🌐 Additional Information from the Web

[Only relevant web information]

## 💡 Key Takeaways

[Short summary]

============================================================
PREVIOUS CONVERSATION
============================================================

{chat_history_text}

============================================================
PDF CONTEXT
============================================================

{pdf_context}

============================================================
WEB CONTEXT
============================================================

{web_context}

============================================================
CURRENT QUESTION
============================================================

{data.question}

============================================================
ANSWER
============================================================
"""

    # ========================================================
    # WEB SEARCH OFF — STRICT PDF MODE
    # ========================================================

    else:

        prompt = f"""
You are a strict PDF-based AI Research Assistant.

Answer the user's CURRENT question using ONLY the
PDF CONTEXT.

You may use the PREVIOUS CONVERSATION ONLY to understand
what words such as "it", "this", "that", "they", or
"the method" refer to.

Previous conversation is NOT evidence.

============================================================
STRICT GROUNDING RULES
============================================================

1. Use ONLY the PDF CONTEXT for factual information.

2. Do NOT use your own general knowledge.

3. Do NOT use information from the internet.

4. Do NOT guess or assume missing information.

5. Do NOT add facts that are not supported by the PDF.

6. Use previous conversation only to resolve references.

7. If the PDF CONTEXT does not contain enough
   information to answer the user's question,
   respond ONLY with:

The available PDF content does not contain enough
information to answer this question.

8. If rule 7 applies, DO NOT provide:
   - Key Takeaways
   - Summary
   - Related information
   - Guesses
   - Additional facts
   - Citations
   - Sources

9. If the PDF contains enough information,
   answer directly and clearly.

10. Keep the answer directly related to the question.

============================================================
ANSWER FORMAT
============================================================

IF THE PDF CONTAINS ENOUGH INFORMATION:

## 📄 Information from the PDF

[Answer using ONLY the PDF context]

## 💡 Key Takeaways

[2–4 points directly related to the answer]

IF THE PDF DOES NOT CONTAIN ENOUGH INFORMATION:

The available PDF content does not contain enough
information to answer this question.

DO NOT ADD ANYTHING ELSE.

============================================================
PREVIOUS CONVERSATION
============================================================

{chat_history_text}

============================================================
PDF CONTEXT
============================================================

{pdf_context}

============================================================
CURRENT QUESTION
============================================================

{data.question}

============================================================
ANSWER
============================================================
"""

    # ========================================================
    # GENERATE FINAL ANSWER
    # ========================================================

    try:

        response = llm.invoke(
            prompt
        )

        final_answer = response.content.strip()

        # ====================================================
        # DETECT UNSUPPORTED ANSWER
        # ====================================================

        no_answer_phrases = [
            "the available pdf content does not contain enough information",
            "the answer could not be found in the uploaded documents",
            "does not contain enough information to answer"
        ]

        is_no_answer = any(
            phrase in final_answer.lower()
            for phrase in no_answer_phrases
        )

        # ====================================================
        # RETURN CLEAN NO-ANSWER RESPONSE
        # ====================================================

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
        # NORMAL ANSWER
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
            e
        )

        return {
            "error": str(e),
            "sources": [],
            "web_sources": []
        }