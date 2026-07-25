function Sidebar() {
  return (
    <div className="w-64 bg-white shadow-md p-5">
      <h2 className="text-xl font-bold mb-6">Documents</h2>

      <ul className="space-y-3">
        <li className="p-3 rounded-lg bg-gray-100 hover:bg-blue-100 cursor-pointer">
          📄 AI Notes.pdf
        </li>

        <li className="p-3 rounded-lg bg-gray-100 hover:bg-blue-100 cursor-pointer">
          📄 React Guide.pdf
        </li>

        <li className="p-3 rounded-lg bg-gray-100 hover:bg-blue-100 cursor-pointer">
          📄 Machine Learning.pdf
        </li>
      </ul>
    </div>
  );
}

export default Sidebar;