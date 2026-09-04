import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listContracts } from "../api";

function ContractsPage() {
  const [contracts, setContracts] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    listContracts().then(setContracts).catch((requestError) => setError(requestError.message));
  }, []);

  return (
    <section>
      <h2>Saved contracts</h2>
      {error && <p className="error">{error}</p>}
      {!error && contracts.length === 0 && <p>No contracts stored yet.</p>}
      {contracts.map((contract) => (
        <article key={contract.id}>
          <div>
            <strong>{contract.lessee}</strong>
            <small>{contract.lessor}</small>
          </div>
          <Link to={`/contracts/${contract.id}`}>View details</Link>
        </article>
      ))}
    </section>
  );
}

export default ContractsPage;
