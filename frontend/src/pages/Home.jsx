import { useState, useRef, useEffect } from "react";
import axios from "axios";

import Sidebar from "../components/Sidebar";
import UploadBox from "../components/UploadBox";

function Home() {
  const [question, setQuestion] = useState("");
  const [useWeb, setUseWeb] = useState(false);

  // ============================================================
  // SELECTED PDF DOCUMENTS
  // ============================================================

  const [selectedDocuments, setSelectedDocuments] = useState([]);

  // ============================================================
  // CHAT MESSAGES
  // ============================================================

  const [messages, setMessages] = useState([
    {
      sender: "ai",
      text: "Hello! Upload a PDF and ask me anything.",
      sources: [],
      webSources: [],
    },
  ]);

  const [loading, setLoading] = useState(false);

  const chatEndRef = useRef(null);

  // ============================================================
  // ASK QUESTION
  // ============================================================

  const askQuestion = async () => {
    if (!question.trim()) {
      alert("Please enter a question.");
      return;
    }

    const currentQuestion = question.trim();

    try {
      setLoading(true);

      // ========================================================
      // BUILD CHAT HISTORY
      // Only send actual user/AI conversation text.
      // ========================================================

      const chatHistory = messages.map((message) => ({
        sender: message.sender,
        text: message.text,
      }));

      const response = await axios.post(
        "http://127.0.0.1:8000/ask",
        {
          question: currentQuestion,
          use_web: useWeb,
          selected_documents: selectedDocuments,
          chat_history: chatHistory,
        }
      );

      console.log(
        "ASK RESPONSE:",
        response.data
      );

      // ========================================================
      // ADD USER + AI MESSAGES
      // ========================================================

      setMessages((prev) => [
        ...prev,

        {
          sender: "user",
          text: currentQuestion,
        },

        {
          sender: "ai",
          text: response.data.answer,
          sources:
            response.data.sources || [],
          webSources:
            response.data.web_sources || [],
        },
      ]);

      setQuestion("");

    } catch (error) {

      console.error(
        "Question error:",
        error
      );

      if (error.response) {

        alert(
          JSON.stringify(
            error.response.data
          )
        );

      } else {

        alert(error.message);

      }

    } finally {

      setLoading(false);

    }
  };


  // ============================================================
  // CLEAR CHAT
  // ============================================================

  const clearChat = () => {

    setMessages([
      {
        sender: "ai",
        text: "Hello! Upload a PDF and ask me anything.",
        sources: [],
        webSources: [],
      },
    ]);

    setQuestion("");
  };


  // ============================================================
  // AUTO SCROLL CHAT
  // ============================================================

  useEffect(() => {

    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });

  }, [messages]);


  // ============================================================
  // UI
  // ============================================================

  return (

    <div className="flex">

      {/* ===================================================== */}
      {/* SIDEBAR */}
      {/* ===================================================== */}

      <Sidebar />


      {/* ===================================================== */}
      {/* MAIN CONTENT */}
      {/* ===================================================== */}

      <div className="flex-1 p-8">

        {/* ================================================= */}
        {/* UPLOAD / DOCUMENT LIBRARY */}
        {/* ================================================= */}

        <UploadBox
          selectedDocuments={
            selectedDocuments
          }
          setSelectedDocuments={
            setSelectedDocuments
          }
        />


        {/* ================================================= */}
        {/* CHAT */}
        {/* ================================================= */}

        <div className="mt-8 bg-white rounded-xl shadow-lg p-6">

          <h2 className="text-2xl font-bold mb-4">
            Chat with your PDF
          </h2>


          {/* ================================================= */}
          {/* CURRENT RAG SELECTION */}
          {/* ================================================= */}

          <div className="mb-5 bg-blue-50 border border-blue-200 rounded-xl p-4">

            <p className="font-semibold text-blue-700">
              🎯 RAG Document Selection
            </p>

            {selectedDocuments.length === 0 ? (

              <p className="text-sm text-blue-600 mt-1">
                All uploaded PDFs will be searched.
              </p>

            ) : (

              <div className="mt-2">

                <p className="text-sm text-blue-600">
                  Searching only:
                </p>

                <div className="mt-2 space-y-1">

                  {selectedDocuments.map(
                    (filename) => (

                      <p
                        key={filename}
                        className="text-sm font-semibold text-blue-800"
                      >
                        📄 {filename}
                      </p>

                    )
                  )}

                </div>

              </div>

            )}

          </div>


          {/* ================================================= */}
          {/* CHAT HISTORY */}
          {/* ================================================= */}

          <div className="space-y-4 mb-6 h-[400px] overflow-y-auto pr-2">

            {messages.map(
              (msg, index) => (

                <div
                  key={index}
                  className={`flex ${
                    msg.sender === "user"
                      ? "justify-end"
                      : "justify-start"
                  }`}
                >

                  <div
                    className={`max-w-[75%] rounded-2xl px-5 py-3 shadow-md ${
                      msg.sender === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >

                    {/* SENDER */}

                    <p className="text-xs font-semibold mb-2 opacity-70">

                      {msg.sender === "user"
                        ? "👤 You"
                        : "🤖 AI Assistant"}

                    </p>


                    {/* ANSWER */}

                    <p className="whitespace-pre-wrap leading-relaxed">
                      {msg.text}
                    </p>


                    {/* ================================================= */}
                    {/* PDF SOURCES */}
                    {/* ================================================= */}

                    {msg.sender === "ai" &&
                      msg.sources?.length > 0 && (

                        <div className="mt-4 border-t pt-4">

                          <p className="font-semibold text-sm mb-3">
                            📚 PDF Sources
                          </p>

                          <div className="space-y-2">

                            {msg.sources.map(
                              (
                                source,
                                sourceIndex
                              ) => (

                                <div
                                  key={
                                    sourceIndex
                                  }
                                  className="bg-white border border-gray-200 rounded-lg p-3"
                                >

                                  <p className="text-sm font-semibold text-gray-800">

                                    📄{" "}
                                    {source.source}

                                  </p>

                                  {source.pages &&
                                    source.pages.length >
                                      0 && (

                                      <p className="text-xs text-gray-500 mt-1">

                                        📑 Pages:{" "}

                                        {source.pages.join(
                                          ", "
                                        )}

                                      </p>

                                    )}

                                </div>

                              )
                            )}

                          </div>

                        </div>

                      )}


                    {/* ================================================= */}
                    {/* WEB SOURCES */}
                    {/* ================================================= */}

                    {msg.sender === "ai" &&
                      msg.webSources?.length > 0 && (

                        <div className="mt-4 border-t pt-4">

                          <p className="font-semibold text-sm mb-3">
                            🌐 Web Sources
                          </p>

                          <div className="space-y-2">

                            {msg.webSources.map(
                              (
                                source,
                                sourceIndex
                              ) => (

                                <a
                                  key={
                                    sourceIndex
                                  }
                                  href={
                                    source.url
                                  }
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="block bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm text-blue-600 hover:bg-blue-100 hover:underline"
                                >

                                  🔗{" "}
                                  {source.title}

                                </a>

                              )
                            )}

                          </div>

                        </div>

                      )}

                  </div>

                </div>

              )
            )}

            <div ref={chatEndRef}></div>

          </div>


          {/* ================================================= */}
          {/* WEB SEARCH TOGGLE */}
          {/* ================================================= */}

          <div className="mb-4">

            <label className="flex items-center gap-2 text-gray-700 cursor-pointer">

              <input
                type="checkbox"
                checked={useWeb}
                onChange={(e) =>
                  setUseWeb(
                    e.target.checked
                  )
                }
                className="w-4 h-4"
              />

              🌐 Use Web Search

            </label>

          </div>


          {/* ================================================= */}
          {/* QUESTION */}
          {/* ================================================= */}

          <textarea
            value={question}
            onChange={(e) =>
              setQuestion(
                e.target.value
              )
            }
            placeholder="Ask a question about your PDF..."
            className="w-full border rounded-lg p-3 h-32 resize-none"
          />


          {/* ================================================= */}
          {/* BUTTONS */}
          {/* ================================================= */}

          <div className="mt-4 flex gap-4">

            <button
              onClick={askQuestion}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg flex items-center gap-2"
            >

              {loading ? (

                <>

                  <svg
                    className="animate-spin h-5 w-5"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >

                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />

                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                    />

                  </svg>

                  Thinking...

                </>

              ) : (

                "Send"

              )}

            </button>


            <button
              onClick={clearChat}
              className="bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-lg"
            >
              🗑 Clear Chat
            </button>

          </div>

        </div>

      </div>

    </div>
  );
}

export default Home;