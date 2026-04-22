import FileUploader from "../components/FileUploader.jsx";
import ResponseCard from "../components/ResponseCard.jsx";

export default function Upload({ projectId, onProjectReady }) {
  function handleUploaded(result) {
    onProjectReady(result.project_id);
  }

  return (
    <div className="page-stack">
      <header>
        <p className="eyebrow">Ingestion</p>
        <h2>Index a codebase.</h2>
        <p className="lead">Upload a ZIP or import a GitHub repository. The backend filters, chunks, embeds, and stores searchable code context.</p>
      </header>

      <FileUploader onUploaded={handleUploaded} />

      <ResponseCard title="Active Project">
        <code>{projectId || "No project indexed yet."}</code>
      </ResponseCard>
    </div>
  );
}
