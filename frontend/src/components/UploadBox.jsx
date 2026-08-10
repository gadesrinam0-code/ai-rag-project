import { useState } from "react";
import axios from "axios";

function UploadBox({
  selectedDocuments,
  setSelectedDocuments,
}) {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [deletingFile, setDeletingFile] = useState(null);

  const [uploadInfo, setUploadInfo] = useState({
    totalFiles: 0,
    totalPages: 0,
    chunks: 0,
  });

  // ============================================================
  // UPLOAD PDFs
  // ============================================================

  const handleUpload = async (event) => {
    const files = Array.from(event.target.files);

    if (files.length === 0) {
      alert("Please select at least one PDF.");
      return;
    }

    const invalidFiles = files.filter(
      (file) => file.type !== "application/pdf"
    );

    if (invalidFiles.length > 0) {
      alert("Please select PDF files only.");
      return;
    }

    setUploading(true);

    const formData = new FormData();

    files.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const response = await axios.post(
        "https://ai-rag-project-production.up.railway.app/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log("UPLOAD RESPONSE:", response.data);

      const uploadedDocuments =
        response.data.document_stats || [];

      setDocuments(uploadedDocuments);

      setUploadInfo({
        totalFiles:
          response.data.total_files || 0,

        totalPages:
          response.data.total_pages || 0,

        chunks:
          response.data.chunks || 0,
      });

      /*
       * Keep only selections that still exist.
       */
      setSelectedDocuments((previous) =>
        previous.filter((name) =>
          uploadedDocuments.some(
            (doc) => doc.filename === name
          )
        )
      );

      alert(response.data.message);

    } catch (error) {
      console.error(
        "Upload error:",
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
      setUploading(false);
      event.target.value = "";
    }
  };


  // ============================================================
  // TOGGLE PDF SELECTION
  // ============================================================

  const toggleDocument = (filename) => {
    setSelectedDocuments((previous) => {

      if (previous.includes(filename)) {

        return previous.filter(
          (name) => name !== filename
        );

      }

      return [
        ...previous,
        filename,
      ];
    });
  };


  // ============================================================
  // SELECT ALL
  // ============================================================

  const selectAllDocuments = () => {
    setSelectedDocuments(
      documents.map(
        (document) => document.filename
      )
    );
  };


  // ============================================================
  // CLEAR SELECTION
  // ============================================================

  const clearSelection = () => {
    setSelectedDocuments([]);
  };


  // ============================================================
  // DELETE DOCUMENT
  // ============================================================

  const handleDelete = async (filename) => {

    const confirmed = window.confirm(
      `Are you sure you want to delete "${filename}"?`
    );

    if (!confirmed) {
      return;
    }

    setDeletingFile(filename);

    try {

      const response = await axios.delete(
        `https://ai-rag-project-production.up.railway.app/delete/${encodeURIComponent(filename)}`
        
      );

      console.log(
        "DELETE RESPONSE:",
        response.data
      );

      if (!response.data.success) {

        alert(
          response.data.message ||
            "Delete failed."
        );

        return;
      }

      const updatedDocuments =
        response.data.document_stats || [];

      setDocuments(
        updatedDocuments
      );

      setUploadInfo({
        totalFiles:
          response.data.total_files || 0,

        totalPages:
          response.data.total_pages || 0,

        chunks:
          response.data.chunks || 0,
      });

      // Remove deleted PDF from selection
      setSelectedDocuments((previous) =>
        previous.filter(
          (name) => name !== filename
        )
      );

      alert(
        response.data.message
      );

    } catch (error) {

      console.error(
        "Delete error:",
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

      setDeletingFile(null);

    }
  };


  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="space-y-6">

      {/* ================================================= */}
      {/* DOCUMENT LIBRARY */}
      {/* ================================================= */}

      <div className="bg-white rounded-2xl shadow-lg p-6">

        <h2 className="text-2xl font-bold text-gray-800">
          📚 Document Library
        </h2>

        <p className="text-gray-500 mt-1">
          Upload PDF documents and choose which
          documents the RAG should use.
        </p>


        {/* ================================================= */}
        {/* UPLOAD AREA */}
        {/* ================================================= */}

        <label
          htmlFor="pdf-upload"
          className="block mt-5 cursor-pointer"
        >

          <div className="border-2 border-dashed border-blue-300 rounded-xl p-8 text-center hover:bg-blue-50 transition">

            <div className="text-4xl mb-3">
              📄
            </div>

            <p className="text-lg font-semibold text-gray-700">

              {uploading
                ? "Uploading and processing..."
                : "Click to upload PDF documents"}

            </p>

            <p className="text-sm text-gray-500 mt-2">
              You can select multiple PDF files
            </p>

          </div>

          <input
            id="pdf-upload"
            type="file"
            accept=".pdf,application/pdf"
            multiple
            onChange={handleUpload}
            className="hidden"
          />

        </label>

      </div>


      {/* ================================================= */}
      {/* DOCUMENT LIST */}
      {/* ================================================= */}

      {documents.length > 0 && (

        <div className="bg-white rounded-2xl shadow-lg p-6">

          {/* HEADER */}

          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-5">

            <div>

              <h3 className="text-xl font-bold text-gray-800">
                📄 Uploaded Documents
              </h3>

              <p className="text-sm text-gray-500">
                Select the documents you want the RAG
                system to search.
              </p>

            </div>


            {/* DOCUMENT COUNT */}

            <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-semibold">

              {documents.length}{" "}

              {documents.length === 1
                ? "Document"
                : "Documents"}

            </span>

          </div>


          {/* ================================================= */}
          {/* SELECTION CONTROLS */}
          {/* ================================================= */}

          <div className="flex flex-wrap items-center gap-3 mb-5">

            <button
              type="button"
              onClick={selectAllDocuments}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold"
            >
              ✓ Select All
            </button>


            <button
              type="button"
              onClick={clearSelection}
              className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-semibold"
            >
              Clear Selection
            </button>

          </div>


          {/* ================================================= */}
          {/* SELECTION STATUS */}
          {/* ================================================= */}

          <div className="mb-5 bg-blue-50 border border-blue-200 rounded-xl p-4">

            <p className="text-sm font-semibold text-blue-700">

              🎯{" "}

              {selectedDocuments.length === 0
                ? "All documents will be searched"
                : `${selectedDocuments.length} document${
                    selectedDocuments.length > 1
                      ? "s"
                      : ""
                  } selected for RAG`}

            </p>

            {selectedDocuments.length === 0 && (

              <p className="text-xs text-blue-600 mt-1">
                Select one or more PDFs to restrict
                the RAG search.
              </p>

            )}

          </div>


          {/* ================================================= */}
          {/* DOCUMENT CARDS */}
          {/* ================================================= */}

          <div className="space-y-4">

            {documents.map(
              (document, index) => {

                const isSelected =
                  selectedDocuments.includes(
                    document.filename
                  );

                const isDeleting =
                  deletingFile ===
                  document.filename;

                return (

                  <div
                    key={`${document.filename}-${index}`}
                    className={`border rounded-xl p-4 transition ${
                      isSelected
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:border-blue-300"
                    }`}
                  >

                    {/* TOP ROW */}

                    <div className="flex items-center gap-4">

                      {/* CHECKBOX */}

                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() =>
                          toggleDocument(
                            document.filename
                          )
                        }
                        disabled={
                          deletingFile !== null
                        }
                        className="w-5 h-5 accent-blue-600 cursor-pointer"
                      />


                      {/* PDF ICON */}

                      <div className="w-12 h-12 rounded-xl bg-red-100 flex items-center justify-center text-2xl">
                        📄
                      </div>


                      {/* NAME */}

                      <div className="flex-1 min-w-0">

                        <p className="font-semibold text-gray-800 truncate">
                          {document.filename}
                        </p>

                        <p className="text-xs text-gray-500 mt-1">
                          PDF Research Document
                        </p>

                      </div>


                      {/* STATUS */}

                      <div className="text-green-600 text-sm font-semibold">

                        ✓ Ready

                      </div>

                    </div>


                    {/* ================================================= */}
                    {/* DETAILS + DELETE */}
                    {/* ================================================= */}

                    <div className="mt-4 flex flex-wrap items-center justify-between gap-3">

                      <div className="flex flex-wrap gap-3">

                        {/* PAGES */}

                        <div className="bg-purple-50 border border-purple-100 rounded-lg px-4 py-2">

                          <p className="text-xs text-gray-500">
                            Pages
                          </p>

                          <p className="font-bold text-purple-700">
                            📑 {document.pages}
                          </p>

                        </div>


                        {/* CHUNKS */}

                        <div className="bg-green-50 border border-green-100 rounded-lg px-4 py-2">

                          <p className="text-xs text-gray-500">
                            RAG Chunks
                          </p>

                          <p className="font-bold text-green-700">
                            🧩 {document.chunks}
                          </p>

                        </div>

                      </div>


                      {/* DELETE */}

                      <button
                        type="button"
                        onClick={() =>
                          handleDelete(
                            document.filename
                          )
                        }
                        disabled={
                          deletingFile !== null
                        }
                        className="bg-red-500 hover:bg-red-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-semibold transition"
                      >

                        {isDeleting
                          ? "Deleting..."
                          : "🗑 Delete"}

                      </button>

                    </div>

                  </div>

                );
              }
            )}

          </div>

        </div>

      )}


      {/* ================================================= */}
      {/* EMPTY STATE */}
      {/* ================================================= */}

      {documents.length === 0 &&
        !uploading && (

          <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center">

            <p className="text-gray-500">
              No documents in your knowledge base yet.
            </p>

          </div>

        )}


      {/* ================================================= */}
      {/* STATISTICS */}
      {/* ================================================= */}

      {documents.length > 0 && (

        <div>

          <h3 className="text-lg font-bold text-gray-800 mb-3">
            📊 Knowledge Base Statistics
          </h3>


          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

            {/* DOCUMENTS */}

            <div className="bg-white rounded-xl shadow-md p-5 border border-gray-100">

              <p className="text-sm text-gray-500">
                Documents
              </p>

              <p className="text-3xl font-bold text-blue-600 mt-1">
                {uploadInfo.totalFiles}
              </p>

            </div>


            {/* PAGES */}

            <div className="bg-white rounded-xl shadow-md p-5 border border-gray-100">

              <p className="text-sm text-gray-500">
                Total Pages
              </p>

              <p className="text-3xl font-bold text-purple-600 mt-1">
                {uploadInfo.totalPages}
              </p>

            </div>


            {/* CHUNKS */}

            <div className="bg-white rounded-xl shadow-md p-5 border border-gray-100">

              <p className="text-sm text-gray-500">
                RAG Chunks
              </p>

              <p className="text-3xl font-bold text-green-600 mt-1">
                {uploadInfo.chunks}
              </p>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}

export default UploadBox;