import React from "react";

export default function FileUpload({ onUpload }) {
  const [file, setFile] = React.useState(null);

  const handleUpload = () => {
    if (!file) return;
    onUpload(file);
  };

  return (
    <div className="bg-white shadow-md rounded-xl p-6">
      <input
        type="file"
        accept=".json"
        onChange={(e) => setFile(e.target.files[0])}
        className="w-full"
      />

      <button
        onClick={handleUpload}
        className="mt-4 bg-primary text-white px-4 py-2 rounded-lg hover:bg-accent"
      >
        Upload SysML Model
      </button>
    </div>
  );
}
