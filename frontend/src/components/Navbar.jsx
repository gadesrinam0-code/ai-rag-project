function Navbar() {
  return (
    <nav className="bg-blue-600 text-white p-4 shadow-md">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <h1 className="text-xl font-bold">📚 AI Knowledge Base Search</h1>

        <button className="bg-white text-blue-600 px-4 py-2 rounded-lg hover:bg-gray-100">
          Upload PDF
        </button>
      </div>
    </nav>
  );
}

export default Navbar;