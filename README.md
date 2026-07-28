# AI RAG Project

An AI-powered Retrieval-Augmented Generation (RAG) application that allows users to upload PDF documents and ask questions about their content.

## Features

- Upload PDF documents
- Extract text from PDFs
- Split text into chunks
- Generate embeddings using Hugging Face
- Store embeddings in FAISS vector database
- Retrieve relevant context
- Answer questions using Groq LLM
- Modern React frontend
- FastAPI backend
- Live deployment with Vercel and Railway

---

## Tech Stack

### Frontend
- React
- Vite
- Axios
- Tailwind CSS

### Backend
- FastAPI
- LangChain
- FAISS
- Hugging Face Embeddings
- Groq LLM
- PyPDF

---

## Project Structure

```
ai-rag-project
│
├── frontend
│   ├── src
│   ├── public
│   └── package.json
│
├── backend
│   ├── app.py
│   ├── requirements.txt
│   └── uploads
│
└── README.md
```

---

## How It Works

1. User uploads a PDF.
2. Text is extracted from the PDF.
3. The text is split into smaller chunks.
4. Hugging Face generates vector embeddings.
5. FAISS stores the embeddings.
6. User asks a question.
7. FAISS retrieves the most relevant chunks.
8. Groq LLM generates an answer using the retrieved context.

---

## Live Demo

### Frontend
https://ai-rag-project-psi.vercel.app

### Backend
https://ai-rag-project-production.up.railway.app

---

## Future Improvements

- Multiple PDF support
- User authentication
- Chat history
- PDF highlighting
- Voice input
- Multi-language support

---

## Author

**Srinam Gade**

AI RAG Project using React, FastAPI, FAISS, Hugging Face Embeddings, and Groq.
