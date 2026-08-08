import { useState } from "react";
import axios from "axios";

function UploadBox() {
  const [fileNames, setFileNames] = useState([]);

  const handleUpload = async (event) => {
    const files = Array.from(event.target.files);

    if (files.length === 0) {
      alert("Please select at least one PDF.");
      return;
    }

    setFileNames(files.map((file) => file.name));

    const formData = new FormData();

    files.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/upload",
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
    <div className="space-y-4">
      <input
        type="file"
        accept=".pdf"
        multiple
        onChange={handleUpload}
      />

      {fileNames.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 shadow-sm">
          <p className="text-sm text-gray-500">
            Uploaded Documents
          </p>

          <div className="mt-2 space-y-1">
            {fileNames.map((name, index) => (
              <p
                key={index}
                className="text-blue-700 font-semibold"
              >
                📄 {name}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default UploadBox;