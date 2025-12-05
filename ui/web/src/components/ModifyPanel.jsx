import React from "react";

export default function ModifyPanel({ onSubmit }) {
  const [text, setText] = React.useState("");
  const [file, setFile] = React.useState(null);

  const handleSend = () => {
    onSubmit(text, file);
    setText("");
  };

  return (
    <div className="mt-4 bg-white border border-gray-200 p-4 rounded-xl shadow">
      <h3 className="text-lg font-semibold text-primary">Modify Output</h3>

      <textarea
        className="w-full mt-2 p-2 border rounded-lg bg-softgray"
        rows="4"
        placeholder="Write feedback for LLM..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <div className="mt-3">
        <input
          type="file"
          onChange={(e) => setFile(e.target.files[0])}
          className="block w-full text-sm text-gray-700"
        />
      </div>

      <button
        onClick={handleSend}
        className="mt-3 bg-accent px-4 py-2 rounded-lg text-primary font-bold hover:opacity-80 transition"
      >
        Send
      </button>
    </div>
  );
}
