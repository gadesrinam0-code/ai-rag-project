import { useState } from "react";
import axios from "axios";

function UploadBox() {
  const [fileName, setFileName] = useState("");

  const handleUpload = async (event) => {
    const file = event.target.files[0];

    if (!file) {
      alert("Please select a PDF.");
      return;
    }

    // Save uploaded file name
    setFileName(file.name);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "https://ai-rag-project-vhp0.onrender.com/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log(response.data);

      alert(response.data.message);
    } catch (error) {
      console.error(error);

      if (error.response) {
        alert(JSON.stringify(error.response.data));
      } else {
        alert(error.message);
      }
    }
  };

  return (
    <div className="mb-6">
      <input
        type="file"
        accept=".pdf"
        onChange={handleUpload}
        className="mb-4"
      />

      {fileName && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 shadow-sm">
          <p className="text-sm text-gray-500">
            Uploaded Document
          </p>

          <p className="text-blue-700 font-semibold mt-1">
            📄 {fileName}
          </p>
        </div>
      )}
    </div>
  );
}

export default UploadBox;