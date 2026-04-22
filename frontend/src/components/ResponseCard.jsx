export default function ResponseCard({ title, children }) {
  if (!children) {
    return null;
  }

  return (
    <article className="response-card">
      <h3>{title}</h3>
      <div>{children}</div>
    </article>
  );
}
