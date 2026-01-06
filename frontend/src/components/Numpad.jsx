import React from "react";

export default function Numpad({ value, onChange, onClose }) {
  const handleClick = (val) => {
    if (val === "C") {
      onChange("");
    } else if (val === "←") {
      onChange(value.slice(0, -1));
    } else if (val === "OK") {
      onClose();
    } else {
      // Only allow one dot
      if (val === "." && value.includes(".")) return;
      onChange(value + val);
    }
  };

  const keys = [
    ["7", "8", "9"],
    ["4", "5", "6"],
    ["1", "2", "3"],
    ["0", ".", "←"],
    ["C", "OK"]
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
      <div className="bg-zinc-800 rounded-lg p-4 w-64 shadow-lg flex flex-col items-center">
        <input
          className="mb-3 w-full text-center text-2xl p-2 rounded bg-zinc-900 text-zinc-100 border border-zinc-700"
          value={value}
          readOnly
        />
        <div className="grid grid-cols-3 gap-2 w-full mb-2">
          {keys.slice(0, 4).flat().map((k, i) => (
            <button
              key={i}
              className="bg-blue-700 text-zinc-100 text-xl rounded p-3 hover:bg-blue-500 transition"
              onClick={() => handleClick(k)}
            >
              {k}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-2 w-full">
          {keys[4].map((k, i) => (
            <button
              key={i}
              className={`rounded p-3 text-xl ${k === "OK" ? "bg-green-600 hover:bg-green-500" : "bg-red-700 hover:bg-red-600"} text-zinc-100 transition`}
              onClick={() => handleClick(k)}
            >
              {k}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
