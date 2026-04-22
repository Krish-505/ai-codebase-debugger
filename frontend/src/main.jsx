import React, { useState } from "react";
import { createRoot } from "react-dom/client";

import Chat from "./pages/Chat.jsx";
import Debug from "./pages/Debug.jsx";
import Upload from "./pages/Upload.jsx";
import "./styles.css";

function App() {
  const [activePage, setActivePage] = useState("upload");
  const [projectId, setProjectId] = useState("");

  const pages = {
    upload: <Upload projectId={projectId} onProjectReady={setProjectId} />,
    chat: <Chat projectId={projectId} onProjectChange={setProjectId} />,
    debug: <Debug projectId={projectId} onProjectChange={setProjectId} />,
  };

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">AI Codebase Assistant</p>
          <h1>Debug with repository context.</h1>
        </div>
        <nav className="nav-list" aria-label="Primary">
          <button className={activePage === "upload" ? "active" : ""} onClick={() => setActivePage("upload")}>
            Upload
          </button>
          <button className={activePage === "chat" ? "active" : ""} onClick={() => setActivePage("chat")}>
            Chat
          </button>
          <button className={activePage === "debug" ? "active" : ""} onClick={() => setActivePage("debug")}>
            Debug
          </button>
        </nav>
        <div className="project-pill">
          <span>Project</span>
          <strong>{projectId || "Not selected"}</strong>
        </div>
      </aside>
      <section className="workspace">{pages[activePage]}</section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
