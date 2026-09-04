import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getContract } from "../api";

function ContractDetailsPage() {
  const { id } = useParams();
  const [contract, setContract] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getContract(id).then(setContract).catch((requestError) => setError(requestError.message));
  }, [id]);

  return (
    <section>
      <Link to="/contracts">Back to contracts</Link>
      <h2>Contract details</h2>
      {error && <p className="error">{error}</p>}
      {!error && !contract && <p>Loading...</p>}
      {contract && <pre>{JSON.stringify(contract, null, 2)}</pre>}
    </section>
  );
}

export default ContractDetailsPage;
