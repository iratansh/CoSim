# CoSim Web App

React + TypeScript SPA that surfaces the control plane APIs and an embedded IDE constrained to Python and C++ editing.

## Getting started

```bash
npm install
npm run dev
```

Set `VITE_API_BASE_URL` in `.env` (defaults to `/api`, which hits the Vite dev proxy). For direct calls bypassing the proxy, point it to the gateway URL (e.g. `http://localhost:8080`).

## Available scripts

- `npm run dev` – start the Vite development server
- `npm run build` – type-check and produce a production build in `dist`
- `npm run preview` – preview the production build
- `npm run lint` – run ESLint against `src/**/*.{ts,tsx}`

## Monaco IDE support

The IDE exposes only two language tabs:

- Python (`main.py`)
- C++ (`main.cpp`)

Extendors should route persistence events through the sessions/collab services once those backends are wired for shared editing.

## Demo credentials & registration

An admin user is available for quick demos once you run `PYTHONPATH=src python -m co_sim.scripts.seed_admin` from the `backend/` directory. Use:

- **Email:** `admin@cosim.dev`
- **Password:** `adminadmin`

The login page also supports self-service registration if you want to create additional accounts.
