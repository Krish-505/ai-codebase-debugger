import { useState } from "react";

export default function ChatBox({ label, placeholder, buttonText, onSubmit }) {
  const [value, setValue] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (!value.trim()) {
      return;
    }
    await onSubmit(value);
  }

  return (
    <form className="chat-box" onSubmit={handleSubmit}>
      <label>
        {label}
        <textarea value={value} onChange={(event) => setValue(event.target.value)} placeholder={placeholder} rows={7} />
      </label>
      <button type="submit">{buttonText}</button>
    </form>
  );
}
