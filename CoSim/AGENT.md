# AGENTS.md

Cloud Robotics Development Platform — Agent & Architecture Spec

**Scope:** Browser-based collaborative robotics development with  **C++ & Python** , **MuJoCo** and **PyBullet** simulators, focused first on **SLAM** and **RL training** workflows.

---

## 1) Goals & Non-Goals

### Goals

* **Instant, shared environments:** 1-click launch of a collaborative IDE + simulator that multiple users can join to edit code and view the same simulation in real time.
* **Language support:** First-class **C++** (builds, dependencies, debugging) and **Python** (venvs, pip/poetry).
* **Task-focused:** Opinionated templates & tooling for **SLAM** (datasets, rosbag playback, metrics) and **RL** (parallel envs, checkpoints, tensorboard).
* **GPU-aware:** Simple controls to request GPU for RL; CPU-only fast boot for SLAM prototyping.
* **Safe, cost-guarded, scalable:** Strict isolation, quotas, auto-hibernate/teardown, and spot-friendly scheduling.

### Non-Goals (MVP)

* High-fidelity game-engine rendering (Unreal/Unity), photorealistic sim.
* Running every simulator (stick to  **MuJoCo** / **PyBullet** ).
* VR/XR in MVP (plan as expansion; hooks below).

---

## 2) High-Level System

┌──────────────────────────────────── Cloud ────────────────────────────────────┐
│                                 API / Control Plane                          │
│  [API-GW]──►[Auth]──►[Project/Workspace]──►[Session Orchestrator]──►[Billing]│
│                      │                         │             │               │
│                      │                         │             └►[Cost Guard]  │
│                      │                         │                             │
│                      ▼                         ▼                             │
│                [Collab Server]◄───────────[Event Bus]──────────►[Notifications]
│                      │                                                   │     │
│                      ▼                                                   ▼     │
│                           ┌──────────── Data Plane ────────────┐               │
│                           │   Kubernetes (CPU + GPU nodes)     │               │
│                           │  ┌──────────┐   ┌──────────┐       │               │
│  Browser ◄─WebRTC/VNC/WS─►│  │ IDE Pod  │   │ Sim Pod  │  ...  │               │
│  (Monaco/VS Code Web,     │  │ (C++/Py) │   │(MuJoCo/  │       │               │
│   multi-user Yjs CRDT)    │  └──────────┘   │ PyBullet)│       │               │
│                           │   ▲      ▲      └──────────┘       │               │
│                           │   │      │           ▲              │               │
│                           │[Build Agent]   [Python Agent]  [RL/SLAM Agents]    │
│                           └─────────────────────────────────────────────────────┘
│         S3/GCS (files, datasets, checkpoints)  ◄──►  Postgres (auth, meta)     │
└────────────────────────────────────────────────────────────────────────────────┘


---

## 3) Agent Roster (Responsibilities, APIs, Scaling)

All agents communicate over **gRPC** (mTLS) and publish events on **NATS** (or Kafka) topics. Idempotent operations, retries with exponential backoff, and per-tenant rate limits.

### Control-Plane Agents

1. **API-Gateway Agent**
   * **Purpose:** Single entry point (REST/gRPC). Enforces authn/z, quotas, request shaping.
   * **Endpoints (REST):**
     * `POST /sessions` (create), `PATCH /sessions/{id}` (pause/resume/scale), `DELETE /sessions/{id}`
     * `POST /projects` / `POST /workspaces`
     * `POST /runs/build` (C++) / `POST /runs/python` (script/module)
     * `POST /rl/jobs` / `POST /slam/experiments`
   * **Scales:** Horizontally behind ALB/NGINX Ingress.
2. **Auth Agent**
   * **Purpose:** OIDC (Google/GitHub), email+MFA, JWT minting, RBAC (owner/editor/viewer).
   * **Data:** `users`, `orgs`, `memberships`, `api_keys`.
   * **Notes:** Short-lived access tokens; signed URLs for S3.
3. **Project/Workspace Agent**
   * **Purpose:** CRUD projects; bind repositories & datasets; manage workspace metadata.
   * **Data:** `projects`, `workspaces`, `datasets`, `templates`, `secrets` (KMS-encrypted).
   * **Features:** Template hydration (MuJoCo RL, PyBullet RL, SLAM baseline, Empty C++/Py).
4. **Session Orchestrator Agent**
   * **Purpose:** Provision & supervise compute sessions (IDE pod + one or more Sim pods).
   * **Actions:** Pod scheduling (node selectors: cpu/gpu), PVC mount, netpol, TTL, idle timers.
   * **Lifecycle:** `Pending → Pulling → Booting → Ready → Idle(H) → Terminated`.
   * **Events:** `session.created`, `session.ready`, `session.idle`, `session.terminated`.
5. **Billing Agent**
   * **Purpose:** Track CPU/GPU minutes, egress, storage; generate usage records → Stripe.
   * **Controls:** Hard/soft caps per tier; pre-emptive warnings (web/email).
   * **Events:** `usage.threshold.crossed`, `billing.hold`.
6. **Cost Guard Agent**
   * **Purpose:** Policy enforcement for runaway costs.
   * **Policies:** Max concurrent GPU jobs, max pods/org, nightly hibernate windows.
   * **Reactions:** `scale_down`, `pause_session`, `deny_new_gpu_job`.
7. **Collaboration Agent**
   * **Purpose:** Multi-user editing via **Yjs** CRDT + y-websocket; presence, roles, locks.
   * **Scope:** Code, notebooks, config files, and *live sim control doc* (start/stop/reset/seed).
   * **Events:** `doc.updated`, `presence.changed`.
8. **Notification Agent**
   * **Purpose:** Email/Webhook/Discord for job status, grading results, spend alerts.

### Data-Plane Agents

9. **Build Agent (C++)**
   * **Purpose:** Deterministic, cached C++ builds (CMake + clang/gcc).
   * **Features:** Remote build cache (sccache), compile DB export, sanitizer toggles.
   * **API:** `StartBuild(workspaceId, target, toolchain, flags)` → `BuildResult(artifactURI, logs)`.
10. **Python Agent**
    * **Purpose:** Virtual env mgmt (pip/poetry), dependency resolution & caching.
    * **API:** `PrepareEnv(reqs.lock)` → `EnvReady(envId)`; `RunModule(envId, entrypoint)`.
11. **Simulation Agent (MuJoCo/PyBullet)**
    * **Purpose:** Launch/attach simulators; expose control plane (reset/step/render), headless+render modes.
    * **Transport:** **WebRTC** for frames + data channels (control), fallback  **noVNC** .
    * **API:** `StartSim(engine, model, headless, fps, gpuPreferred)`, `Step(actions)`, `Snapshot()`.
12. **RL Agent**
    * **Purpose:** Parallel env orchestration, experience collection, training loops.
    * **Stacks:** MuJoCo (MJX when available), PyBullet; SB3/JAX/PyTorch configurations.
    * **Artifacts:** Checkpoints to S3, TensorBoard streams, eval reports.
    * **API:** `CreateJob(config, resources{gpu:n})` → `JobStatus`, `CancelJob(id)`.
13. **SLAM Agent**
    * **Purpose:** Run SLAM pipelines (e.g., ORB-SLAM2 baselines, LOAM variants) on datasets/rosbags.
    * **Features:** Dataset mounting, trajectory alignment, metrics (ATE/RPE), KITTI/TUM loaders.
    * **API:** `RunExperiment(pipeline, datasetRef, params)` → `Metrics + Artifacts`.
14. **Stream Agent**
    * **Purpose:** WebRTC SFU for video/data (sim frames, IDE port-forward), TURN for NAT.
    * **Fallback:** VNC over WebSocket for non-WebRTC environments.
15. **Snapshot Agent**
    * **Purpose:** On-demand & scheduled workspace snapshots (source + env lockfiles + data refs).
    * **Restore:** Clone to new session (reproducibility & collaboration).
16. **Image Builder Agent**
    * **Purpose:** Bake base images and layer templates (MuJoCo, PyBullet, toolchains).
    * **Pipeline:** GitHub Actions → ECR/GCR; SBOMs, cosign signing.
17. **Abuse Detection Agent**
    * **Purpose:** Crypto-mining & exfil detection (perf signatures, egress profiling).
    * **Actions:** Throttle, suspend, require KYC for reinstatement.
18. **Metrics/Telemetry Agent**
    * **Purpose:** Prometheus exporters; OpenTelemetry traces; per-tenant dashboards.

---

## 4) Frontend & Collaboration

* **Tech:** React + TypeScript,  **Monaco/VS Code Web** , shadcn/ui, Zustand.
* **Collab:** **Yjs** CRDT; presence/awareness; per-file permission overlay; merge-safe binary file locks.
* **Sim View:** WebRTC canvas (H.264/VP9), adjustable FPS & resolution, low-latency control channel.
* **Debug:** C++ (lldb/gdb via webtty), Python (debugpy). Terminal multiplexing per user.
* **“Live Room” model:** Anyone joined sees the same codebase & the same running sim; session owner grants run/step control.

---

## 5) Data Model (selected)

```ts
type Project = {
  id: string; name: string; orgId: string;
  visibility: "private" | "org" | "public";
  createdAt: string; updatedAt: string; templateId?: string;
};

type Workspace = {
  id: string; projectId: string; defaultBranch: string;
  storageGiB: number; env: { language: "cpp"|"python"|"mixed"; toolchain: string; };
};

type Session = {
  id: string; workspaceId: string;
  pods: { idePod: string; simPods: string[]; };
  resources: { cpu: string; mem: string; gpu: number };
  state: "pending"|"ready"|"idle"|"paused"|"terminated";
  idleSeconds: number; lastActiveAt: string;
};

type RLJob = {
  id: string; workspaceId: string; engine: "mujoco"|"pybullet";
  parallelEnvs: number; accel: "cpu"|"gpu"; checkpointURI?: string;
  status: "queued"|"running"|"succeeded"|"failed"|"cancelled";
};

type SLAMRun = {
  id: string; workspaceId: string; pipeline: string; datasetRef: string;
  metrics: { ATE?: number; RPE?: number; fps?: number };
  artifacts: string[];
};
```

---

## 6) Session & Job Flows (happy paths)

### A) Launch shared C++ workspace + MuJoCo sim

1. `POST /sessions` → Orchestrator schedules IDE Pod (CPU) + Sim Pod (CPU|GPU optional).
2. Collab Agent creates Yjs docs for `/` workspace; returns room token(s).
3. Browser establishes WebRTC to  **Stream Agent** ; sim frames begin; controls bound.
4. Build Agent compiles C++ target; artifact hot-reloaded in Sim Pod.
5. Idle timer resets on file edits/stepping; Cost Guard hibernates at threshold.

### B) Start RL job (MuJoCo or PyBullet)

1. `POST /rl/jobs` with `parallelEnvs`, `accel=gpu`, `algo=config`.
2. RL Agent provisions GPU Pod; spins N parallel envs; streams TB logs; checkpoints to S3.
3. On completion, artifacts registered; Notifications emit success + cost usage.

### C) Run SLAM experiment

1. `POST /slam/experiments` with dataset ref + pipeline params.
2. SLAM Agent mounts dataset PVC/read-only S3; runs; computes  **ATE/RPE** ; uploads plots.
3. Report attaches to workspace, shareable link for instructor/peers.

---

## 7) Runtime & Infrastructure

* **Cluster:** Kubernetes (EKS/GKE). Node pools: `cpu-standard`, `gpu-a10/3090/ada`.
* **Containers:** **NVIDIA Container Runtime** for GPU;  **gVisor** /**Kata** for extra isolation.
* **Networking:** CNI (Cilium), per-session NetworkPolicies; egress firewall + TLS everywhere.
* **Storage:** Postgres 15 (Cloud SQL/RDS) for meta; Redis for queues; S3/GCS for files/checkpoints; RWX PVC (CephFS/EFS) for live workspace.
* **Streaming:** **WebRTC SFU** (e.g., ion-sfu or mediasoup) + TURN; fall back  **noVNC** .
* **CI/CD:** GitHub Actions → ECR/GCR; IaC via Terraform; images signed (cosign), SBOM (syft).
* **Observability:** Prometheus + Grafana; Loki; OpenTelemetry traces; SLO dashboards.
* **Security:** mTLS gRPC; JWT with short TTL; KMS-encrypted secrets; OPA/Gatekeeper policies; daily backups.

---

## 8) Images & Tooling Baselines

* **Base OS:** Ubuntu 22.04
* **Toolchains:** clang-17/gcc-12, CMake, Ninja, gdb/lldb
* **Python:** 3.11, pip + uv/poetry, debugpy, numpy/scipy/jax/torch (optional layers)
* **Simulators:**
  * **MuJoCo 3** + mujoco-python bindings, optional **MJX** layer (GPU/TPU accel where available)
  * **PyBullet** + Bullet tools
* **Dev add-ons:** VS Code Server (code-web), zsh/fish, git-lfs, tmux
* **Caches:** sccache (C++), wheels/uv cache (Python)

Layering strategy:

```
base:runtime → base:dev → lang:cpp → lang:python → sim:mujoco | sim:pybullet → template:rl|slam
```

---

## 9) Collaboration Details

* **Documents in CRDT:** `/src/**`, `/notebooks/**`, `/config/**`, `/sim-control.json`.
* **Presence/roles:** owner/editor/viewer; granular file locks for binaries & datasets.
* **Conflict rules:** Text files CRDT-merged; binaries require lock checkout.
* **Sim sync:** `sim-control.json` holds seed, reset flag, scenario id, stepping mode; Sim Agent subscribes to CRDT changes for deterministic shared runs.
* **Annotations:** time-coded comments pinned to frames; export as review report.

---

## 10) Security & Compliance

* **Isolation:** Each session in a dedicated namespace; seccomp/AppArmor profiles; no hostPath.
* **Secrets:** Per-workspace KMS envelope; one-time scoped tokens for data mounts.
* **Data:** At-rest encryption (S3 SSE, encrypted PVCs); in-transit TLS 1.3.
* **Abuse:** Mining signatures, sustained 100% GPU without sim/runs → throttle & flag.
* **Compliance (roadmap):** DPA templates; audit logs; SOC-2 controls.

---

## 11) SLOs & Guardrails

* **Boot time (p95):** CPU session <  **30s** ; GPU-sim <  **60s** .
* **Interactive latency:** WebRTC round-trip < **120ms** intra-region.
* **Cost caps:** Free/student hard caps; pre-emptive pause at 90% quota; org-level GPU concurrency ≤ N.
* **Auto-hibernate:** IDE inactive  **5 min** ; RL/SLAM jobs checkpoint every  **5–10 min** .

---

## 12) Pricing & Quotas (tech levers)

* **Free:** CPU only, 2 vCPU / 4 GB, 20 hrs/mo, 2 GB storage, no GPU.
* **Student:** Up to 4 vCPU / 8 GB,  **optional GPU minutes** , 10 GB storage.
* **Pro/Teams:** Adjustable CPU/GPU; shared storage; concurrency controls.

Agent levers: Billing + Cost Guard enforce pod limits, GPU concurrency, and timeouts.

---

## 13) Failure Modes & Recovery

* **Sim crash:** Supervisor restarts container; last **Snapshot Agent** state reload; user message.
* **GPU eviction/spot loss:** RL Agent auto-restores from last checkpoint; notify.
* **WebRTC blocked:** Fallback to VNC; reduced FPS & bit-rate.
* **Build cache miss:** Warm caches per region via Image Builder nightly jobs.
* **Schema drift:** Versioned APIs; graceful deprecations; feature flags.

---

## 14) VR/XR Expansion Hooks (Post-MVP)

* **Rendering path:** WebXR canvas from Sim Agent (mono → stereo); optional off-screen render farm.
* **Pose I/O:** WebXR device pose → control channel; safety sandbox for inputs.
* **Collab:** Multi-user avatars mapped to CRDT presence; “teaching mode” camera follows owner.

---

## 15) Initial Templates

* **RL (MuJoCo):** PPO/SAC baseline; N-parallel envs; MJX toggle; TB logging.
* **RL (PyBullet):** PPO baseline; URDF loader; curriculum training scaffold.
* **SLAM:** ORB-SLAM2 baseline; KITTI/TUM dataset loaders; eval notebook (ATE/RPE plots).
* **Empty:** Minimal C++ + CMake and Python starter with tests & CI.

---

## 16) Rollout Plan (Infra & Product)

* **Phase 0 (Internal):** CPU-only cluster; PyBullet; Python; basic Yjs collab; WebRTC.
* **Phase 1:** C++ builds + MuJoCo; SLAM agent; dataset mounting; snapshots; quotas.
* **Phase 2:** GPU pool + RL agent; MJX optional; autoscaling + cost guard v2; org workspaces.
* **Phase 3:** Edu features (grading, roster sync), sharing links, public templates; VR tech spike.

---

## 17) Open Questions

* Per-workspace **rootless** container requirement vs privileged GPU runtime: finalize with security.
* SLAM packages that require ROS2—include ROS2 Humble in separate “slam” images or optional layer?
* Determinism guarantees for “shared sim” (seed & physics timesteps) across engines.
* Regional data residency requirements for universities (EU/CA partitions).

---

## 18) Tech Stack Summary

* **Frontend:** React + TS, Monaco/VS Code Web, Yjs, WebRTC, Tailwind/shadcn.
* **Backend:** FastAPI (Python) for APIs & WS; gRPC between agents; Celery/RQ on Redis for jobs.
* **Infra:** Kubernetes, NVIDIA runtime, NATS (events), Postgres, Redis, S3, Prometheus/Grafana/Loki.
* **Sim:** **MuJoCo 3** (+MJX when possible),  **PyBullet** .
* **Langs:** **C++** (clang/gcc, CMake) and **Python** (3.11) as first-class citizens.

---

### TL;DR

This agent architecture keeps the product  **focused and sustainable** : collaborative C++/Python development with **MuJoCo/PyBullet** only, targeted **SLAM** and **RL** workflows, and strong guardrails for  **cost, security, and scalability** . It’s practical to ship in phases, sets a clean foundation for VR/XR later, and directly differentiates on **collaboration + task-specific productivity** rather than attempting to host every simulator.
