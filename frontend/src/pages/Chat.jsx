import { useState } from "react";

import ChatBox from "../components/ChatBox.jsx";
import ResponseCard from "../components/ResponseCard.jsx";
import { askCodebase } from "../services/api.js";

export default function Chat({ projectId, onProjectChange }) {
  const [answer, setAnswer] = useState(null);
  const [status, setStatus] = useState("");

  async function handleQuestion(question) {
    if (!projectId) {
      setStatus("Paste or create a project ID first.");
      return;
    }
    setStatus("Searching code context...");
    try {
      const result = await askCodebase(projectId, question);
      setAnswer(result);
      setStatus("");
    } catch (error) {
      setStatus(error.message);
    }
  }

  return (
    <div className="page-stack">
      <header>
        <p className="eyebrow">Chat</p>
        <h2>Ask about the repository.</h2>
      </header>

      <label className="project-input">
        Project ID
        <input value={projectId} onChange={(event) => onProjectChange(event.target.value)} placeholder="Paste project_id" />
      </label>

      <ChatBox label="Question" placeholder="Explain the auth flow or find where this API route is handled." buttonText="Ask" onSubmit={handleQuestion} />
      {status && <p className="status-line">{status}</p>}

      <ResponseCard title="Answer">
        {answer && <p className="preserve-lines">{answer.answer}</p>}
      </ResponseCard>

      <ResponseCard title="Sources">
        {answer?.sources?.map((source) => (
          <div className="source-row" key={`${source.file_path}-${source.start_line}`}>
            <strong>{source.file_path}</strong>
            <span>
              lines {source.start_line}-{source.end_line}
            </span>
          </div>
        ))}
      </ResponseCard>
    </div>
  );
}
