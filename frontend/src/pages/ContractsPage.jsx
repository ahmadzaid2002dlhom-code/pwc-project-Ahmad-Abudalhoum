import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listContracts } from "../api";

function ContractsPage() {
  const [contracts, setContracts] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listContracts()
      .then(setContracts)
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <h2>Saved contracts</h2>
      {loading && <p>Loading contracts...</p>}
      {!loading && error && <p className="error">{error}</p>}
      {!loading && !error && contracts.length === 0 && <p>No contracts stored yet.</p>}
      {!loading && !error && contracts.map((contract) => (
        <article key={contract.id}>
          <div>
            <strong>Contract #{contract.id}: {contract.lessee}</strong>
            <small>Lessor: {contract.lessor}</small>
            <small>{contract.commencement_date} to {contract.expiration_date}</small>
            <small>
              {contract.currency} {contract.monthly_rent} per month -{" "}
              {contract.contract_duration_days} days
            </small>
          </div>
          <Link to={`/contracts/${contract.id}`}>View details</Link>
        </article>
      ))}
    </section>
  );
}

export default ContractsPage;
