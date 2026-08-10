# 🤖 AI-Powered PDF RAG Assistant

An AI-powered **Retrieval-Augmented Generation (RAG)** application that allows users to upload a PDF, ask questions about its content, and receive detailed, context-aware answers.

The application also provides an optional **Web Search** mode for questions that require current information beyond the uploaded PDF.

## 🚀 Live Demo

* **Frontend:** https://ai-rag-project-gadesrinam0-3714s-projects.vercel.app
* **Backend:** https://ai-rag-project-production.up.railway.app
* **GitHub:** https://github.com/srinamgade/ai-rag-project

---

## 📌 Overview

Understanding long research papers and technical documents can be time-consuming.

This project provides an interactive AI assistant that lets users:

* Upload **one PDF at a time**
* Ask questions about the uploaded document
* Retrieve relevant PDF content using semantic search
* Generate detailed answers using an LLM
* Ask follow-up questions using conversation context
* Enable Web Search for current information
* Retrieve and display relevant PDF source pages

When a new PDF is uploaded, the previously uploaded PDF is replaced.

---

## ❗ Problem Statement

Research papers and technical documents often contain large amounts of information spread across many pages.

Traditional keyword-based searching can make it difficult to find the exact information needed, especially when the user's question uses different wording from the document.

The goal of this project is to provide a conversational interface that can understand a user's question, retrieve the most relevant parts of a PDF, and generate a useful answer based on that retrieved context.

---

## 💡 Solution

The application uses a **Retrieval-Augmented Generation (RAG)** pipeline.

Instead of directly asking an LLM to answer a question, the system:

1. Extracts text from the uploaded PDF.
2. Splits the text into smaller chunks.
3. Converts the chunks into embeddings.
4. Stores the embeddings in FAISS.
5. Retrieves the most relevant chunks for a question.
6. Provides the retrieved context to the LLM.
7. Generates a detailed answer.

When **Web Search** is enabled, Tavily is also used to retrieve additional current information.

---

## 🧠 RAG Architecture

```text
                    ┌──────────────┐
                    │     User     │
                    └──────┬───────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   React UI      │
                  │     Vercel      │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  FastAPI API    │
                  │     Railway     │
                  └────────┬────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       ┌──────────────┐         ┌──────────────┐
       │ PDF Pipeline │         │ Web Search   │
       │              │         │   Tavily     │
       └──────┬───────┘         └──────┬───────┘
              │                        │
              ▼                        │
       ┌──────────────┐                │
       │ Text Chunks  │                │
       └──────┬───────┘                │
              │                        │
              ▼                        │
       ┌──────────────┐                │
       │ HuggingFace  │                │
       │ Embeddings   │                │
       └──────┬───────┘                │
              │                        │
              ▼                        │
       ┌──────────────┐                │
       │    FAISS     │                │
       │ Vector Store │                │
       └──────┬───────┘                │
              │                        │
              └──────────┬─────────────┘
                         ▼
                  ┌──────────────┐
                  │   Groq LLM   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ AI Response  │
                  └──────────────┘
```

---

## ✨ Key Features

### 📄 Single PDF Upload

The application supports **one active PDF at a time**.

Uploading a new PDF replaces the previously uploaded document.

### 🔎 Semantic Retrieval

The system uses embeddings and FAISS vector search to retrieve relevant sections of the PDF based on the meaning of the user's question.

### 🤖 AI-Powered Answers

The retrieved document context is passed to a Groq-powered LLM to generate detailed answers.

### 💬 Follow-Up Questions

The application maintains recent chat history so users can ask follow-up questions naturally.

Example:

```text
User: What are the main contributions of this paper?

User: Why are these contributions important?
```

### 🌐 Web Search

Users can enable **Use Web Search** when they need information that may not be available in the uploaded PDF.

This is especially useful for questions about current or recent developments.

### 📚 Source Information

Retrieved PDF chunks retain their source filename and page number, allowing the application to identify where relevant information came from.

---

## 🛠️ Tech Stack

### Frontend

* React
* JavaScript
* Axios
* Tailwind CSS

### Backend

* Python
* FastAPI
* LangChain

### AI / RAG

* Groq
* HuggingFace Sentence Transformers
* FAISS
* Retrieval-Augmented Generation

### PDF Processing

* PyPDF

### Web Search

* Tavily

### Deployment

* Vercel
* Railway
* GitHub

---

## 🔄 How It Works

### 1. Upload PDF

The user uploads a PDF through the React interface.

### 2. Extract Text

The FastAPI backend extracts text from the PDF using PyPDF.

### 3. Split Text

The extracted content is divided into smaller chunks.

### 4. Generate Embeddings

Each chunk is converted into an embedding using a HuggingFace sentence-transformer model.

### 5. Store in FAISS

The embeddings are stored in a FAISS vector database.

### 6. Ask a Question

The user enters a question in the chat interface.

### 7. Retrieve Relevant Chunks

The system performs semantic similarity search to find relevant PDF content.

### 8. Generate the Answer

The retrieved context is sent to the Groq LLM.

### 9. Optional Web Search

If Web Search is enabled, Tavily retrieves additional relevant information.

### 10. Display the Result

The generated answer is returned to the React frontend and displayed in the chat interface.

---

## 🌐 Web Search Modes

### Web Search OFF

```text
Question
   ↓
FAISS Retrieval
   ↓
Relevant PDF Chunks
   ↓
Groq LLM
   ↓
PDF-Based Answer
```

### Web Search ON

```text
Question
   ↓
PDF Retrieval + Tavily Search
   ↓
PDF Context + Web Context
   ↓
Groq LLM
   ↓
Combined Answer
```

This allows the application to handle both **document-based questions** and questions requiring **current information**.

---

## 🧪 Example Questions

### PDF Questions

```text
What is the main objective of this paper?
```

```text
Explain the main contributions of this paper in detail.
```

```text
What methodology does the paper use?
```

```text
Why are these contributions important?
```

### Web Search Questions

Enable **Use Web Search** and ask:

```text
What are the latest advancements in RAG in 2026?
```

```text
What recent developments are related to this research area?
```

---

## 📂 Project Structure

```text
ai-rag-project/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── uploads/
│   └── faiss_index/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── UploadBox.jsx
│   │   │
│   │   └── pages/
│   │       └── Home.jsx
│   │
│   ├── package.json
│   └── ...
│
├── .gitignore
└── README.md
```

---

## ⚙️ Local Installation

### Clone the repository

```bash
git clone https://github.com/srinamgade/ai-rag-project.git
cd ai-rag-project
```

### Backend Setup

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

### Environment Variables

Create a `.env` file and add your API keys:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

**Never commit API keys to GitHub.**

### Start Backend

```bash
uvicorn backend.app:app --reload
```

### Start Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🚀 Deployment

### Frontend

The React frontend is deployed on **Vercel**.

### Backend

The FastAPI backend is deployed on **Railway**.

### Source Code

The complete project source code is available on **GitHub**.

---

## 📊 Project Highlights

This project demonstrates practical experience with:

* Retrieval-Augmented Generation
* Semantic search
* Vector databases
* Large Language Models
* Prompt engineering
* PDF document processing
* REST APIs
* React development
* Web search integration
* Cloud deployment
* Git and GitHub

---

## 🔮 Future Improvements

Potential future enhancements include:

* Multi-user authentication
* Persistent chat history
* Multiple PDF collections
* PDF comparison
* Citation highlighting
* OCR support for scanned PDFs
* Streaming AI responses
* Improved retrieval and reranking
* Conversation export
* Document management
* RAG evaluation metrics

---

## 👩‍💻 Author

### Srinam Gade

Generative AI / RAG Project

---

## ⭐ Project Links

| Resource         | Link                                             |
| ---------------- | ------------------------------------------------ |
| 🌐 Live Frontend | https://ai-rag-project-psi.vercel.app            |
| ⚙️ Backend API   | https://ai-rag-project-production.up.railway.app |
| 💻 GitHub        | https://github.com/srinamgade/ai-rag-project     |

---

## 📜 License

This project is intended for educational and portfolio purposes.
