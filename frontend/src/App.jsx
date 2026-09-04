import { NavLink, Route, Routes } from "react-router-dom";

import ContractDetailsPage from "./pages/ContractDetailsPage";
import ContractsPage from "./pages/ContractsPage";
import ExtractPage from "./pages/ExtractPage";

function App() {
  return (
    <>
      <header>
        <h1>Lease contracts</h1>
        <nav>
          <NavLink to="/">Extract</NavLink>
          <NavLink to="/contracts">Saved contracts</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<ExtractPage />} />
          <Route path="/contracts" element={<ContractsPage />} />
          <Route path="/contracts/:id" element={<ContractDetailsPage />} />
        </Routes>
      </main>
    </>
  );
}

export default App;
