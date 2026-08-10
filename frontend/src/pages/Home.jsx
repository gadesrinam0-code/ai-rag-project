// Trigger Vercel redeploy
import { useState, useRef, useEffect } from "react";
import axios from "axios";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import UploadBox from "../components/UploadBox";

function Home() {
  const [question, setQuestion] = useState("");
  const [useWeb, setUseWeb] = useState(false);

  const [messages, setMessages] = useState([
    {
      sender: "ai",
      text: "Hello! Upload a PDF and ask me anything.",
    },
  ]);

  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const askQuestion = async () => {
    if (!question.trim()) {
      alert("Please enter a question.");
      return;
    }

    try {
      setLoading(true);

      const response = await axios.post(
        "https://ai-rag-project-production.up.railway.app/ask",
        {
          question: question,
          use_web: useWeb,
        }
      );

      console.log(response.data);

      setMessages((prev) => [
        ...prev,
        {
          sender: "user",
          text: question,
        },
        {
          sender: "ai",
          text: response.data.answer,
        },
      ]);

      setQuestion("");
    } catch (error) {
      console.error(error);

      if (error.response) {
        alert(JSON.stringify(error.response.data));
      } else {
        alert(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        sender: "ai",
        text: "Hello! Upload a PDF and ask me anything.",
      },
    ]);

    setQuestion("");
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  return (
    <>
      <Navbar />

      <div className="flex">
        <Sidebar />

        <div className="flex-1 p-8">
          <UploadBox />

          <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4">
              Chat with your PDF
            </h2>

            {/* Chat History */}
            <div className="space-y-4 mb-6 h-[400px] overflow-y-auto pr-2">
              {messages.map((msg, index) => (
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
                    <p className="text-xs font-semibold mb-2 opacity-70">
                      {msg.sender === "user"
                        ? "👤 You"
                        : "🤖 AI Assistant"}
                    </p>

                    <p className="whitespace-pre-wrap leading-relaxed">
                      {msg.text}
                    </p>
                  </div>
                </div>
              ))}

              <div ref={chatEndRef}></div>
            </div>

            {/* Web Search Toggle */}
            <div className="mb-4">
              <label className="flex items-center gap-2 text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useWeb}
                  onChange={(e) => setUseWeb(e.target.checked)}
                  className="w-4 h-4"
                />
                🌐 Use Web Search
              </label>
            </div>

            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about your PDF..."
              className="w-full border rounded-lg p-3 h-32 resize-none"
            />

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
    </>
  );
}

export default Home;