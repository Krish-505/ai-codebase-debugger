import { useState } from "react";

import { uploadGitHub, uploadZip } from "../services/api.js";

export default function FileUploader({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [status, setStatus] = useState("");

  async function handleZipUpload(event) {
    event.preventDefault();
    if (!file) {
      setStatus("Choose a ZIP file first.");
      return;
    }
    await runUpload(() => uploadZip(file));
  }

  async function handleRepoUpload(event) {
    event.preventDefault();
    if (!repoUrl) {
      setStatus("Enter a GitHub repository URL.");
      return;
    }
    await runUpload(() => uploadGitHub(repoUrl, branch));
  }

  async function runUpload(uploadFn) {
    setStatus("Indexing codebase...");
    try {
      const result = await uploadFn();
      onUploaded(result);
      setStatus(`Indexed ${result.files_indexed} files and ${result.chunks_indexed} chunks.`);
    } catch (error) {
      setStatus(error.message);
    }
  }

  return (
    <div className="split-grid">
      <form className="panel" onSubmit={handleZipUpload}>
        <h2>Upload ZIP</h2>
        <label>
          Codebase archive
          <input type="file" accept=".zip" onChange={(event) => setFile(event.target.files?.[0] || null)} />
        </label>
        <button type="submit">Index ZIP</button>
      </form>

      <form className="panel" onSubmit={handleRepoUpload}>
        <h2>Import GitHub Repo</h2>
        <label>
          Repository URL
          <input value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} placeholder="https://github.com/user/repo" />
        </label>
        <label>
          Branch
          <input value={branch} onChange={(event) => setBranch(event.target.value)} placeholder="main" />
        </label>
        <button type="submit">Index Repo</button>
      </form>

      {status && <p className="status-line">{status}</p>}
    </div>
  );
}
