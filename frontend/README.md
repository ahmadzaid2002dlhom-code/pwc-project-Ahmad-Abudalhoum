# LeaseLens React Frontend

Optional React interface for submitting lease text, viewing validated extraction
results, and browsing stored contracts.

## Setup

Node.js 22 or newer is recommended.

```bash
cd frontend
npm install
```

Copy the environment example:

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

`VITE_API_BASE_URL` must point to the running FastAPI backend. Its default value
is `http://localhost:8000`.

## Run locally

Start the backend from the repository root, then start the frontend:

```bash
npm run dev
```

Open `http://localhost:5173`.

## Production build

```bash
npm run build
npm run preview
```

The production assets are written to `frontend/dist/`.
