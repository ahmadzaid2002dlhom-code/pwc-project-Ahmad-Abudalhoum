import { useState } from "react";

import { extractContract } from "../api";

function ExtractPage() {
  const [text, setText] = useState("");
  const [contract, setContract] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      setContract(await extractContract(text));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2>Extract a lease</h2>
      <form onSubmit={submit}>
        <label htmlFor="contract-text">Contract text</label>
        <textarea
          id="contract-text"
          rows="12"
          required
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <button disabled={loading}>{loading ? "Extracting..." : "Extract"}</button>
      </form>
      {error && <p className="error">{error}</p>}
      {contract && (
        <>
          <h3>Stored contract</h3>
          <pre>{JSON.stringify(contract, null, 2)}</pre>
        </>
      )}
    </section>
  );
}

export default ExtractPage;
