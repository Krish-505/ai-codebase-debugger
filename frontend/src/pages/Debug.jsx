import { useState } from "react";

import ResponseCard from "../components/ResponseCard.jsx";
import { debugCodebase } from "../services/api.js";

export default function Debug({ projectId, onProjectChange }) {
  const [errorMessage, setErrorMessage] = useState("");
  const [stackTrace, setStackTrace] = useState("");
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("");

  async function handleDebug(event) {
    event.preventDefault();
    if (!projectId || !errorMessage.trim()) {
      setStatus("Project ID and error message are required.");
      return;
    }
    setResult(null);
    setStatus("Analyzing failure...");
    try {
      const response = await debugCodebase(projectId, errorMessage, stackTrace);
      setResult(response);
      setStatus("");
    } catch (error) {
      setStatus(error.message);
    }
  }

  return (
    <div className="page-stack">
      <header>
        <p className="eyebrow">Debug Mode</p>
        <h2>Find the likely root cause.</h2>
      </header>

      <form className="debug-form" onSubmit={handleDebug}>
        <label>
          Project ID
          <input value={projectId} onChange={(event) => onProjectChange(event.target.value)} placeholder="Paste project_id" />
        </label>
        <label>
          Error message
          <textarea value={errorMessage} onChange={(event) => setErrorMessage(event.target.value)} rows={4} placeholder="TypeError: Cannot read properties of undefined..." />
        </label>
        <label>
          Stack trace
          <textarea value={stackTrace} onChange={(event) => setStackTrace(event.target.value)} rows={8} placeholder="Paste stack trace here" />
        </label>
        <button type="submit">Analyze</button>
      </form>

      {status && <p className="status-line">{status}</p>}

      <ResponseCard title="Root Cause">
        {result && <p className="preserve-lines">{result.root_cause}</p>}
      </ResponseCard>
      <ResponseCard title="Explanation">
        {result && <p className="preserve-lines">{result.explanation}</p>}
      </ResponseCard>
      <ResponseCard title="Fix Suggestion">
        {result && <p className="preserve-lines">{result.fix_suggestion}</p>}
      </ResponseCard>
      <ResponseCard title="Patch">
        {result?.patch && <pre>{result.patch}</pre>}
      </ResponseCard>

      <ResponseCard title="Sources">
        {result?.sources?.map((source) => (
          <details className="source-detail" key={`${source.file_path}-${source.start_line}-${source.end_line}`}>
            <summary>
              <strong>{source.file_path}</strong>
              <span>
                lines {source.start_line}-{source.end_line}
              </span>
            </summary>
            <pre>{source.content}</pre>
          </details>
        ))}
      </ResponseCard>
    </div>
  );
}
