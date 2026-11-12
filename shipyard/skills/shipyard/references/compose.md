# Writing a compose file for Shipyard

Read this when the repo has no compose file at its root, when `plan_application` returns `add_compose_file`, or when
it says the compose file isn't valid. Shipyard builds every environment from one Docker Compose file.

Never overwrite, replace or silently rewrite a compose file the user already has. Every change is shown as a diff and
made on a branch only after the user says yes.

## 1. Look for an existing file first

`plan_application` only finds `docker-compose.yml`, `docker-compose.yaml`, `compose.yml` or `compose.yaml` at the
repo root. A file anywhere else, or with another name, still counts as "no compose file". Before writing anything,
search the repo (skip `node_modules`, `vendor`, `.git` and build output) for:

- `*compose*.yml` and `*compose*.yaml` (for example `docker-compose.dev.yml`, `deploy/compose.yml`)

Then:

| What you find | What to do |
|---|---|
| One file, elsewhere or under another name | Ask whether it's the app. If yes, offer two ways: rename or move it to `compose.yml` at the root (with their yes, as a commit), or keep it and pass `compose_filename: <path>` to `create_application`. With `compose_filename`, `plan_application` can't preview that file, so its services, routes and env names aren't checked before create: say so. Don't add a root file that uses `include:`, because Shipyard doesn't support it. |
| Several files, or a base file plus overrides | Ask which one describes the app. Don't merge them yourself. |
| A file `plan_application` called invalid | Show the reason it gave, offer the smallest fix to that file, and plan again. |
| A file that only works locally (see section 5) | Point out each problem and propose edits as a diff. |
| None | Write one, from section 2. |

## 2. Analyze the repo

Work out, and show the user before writing anything:

- **What runs.** Each part that runs on its own: a web frontend, an API, a worker, a scheduled job. Read
  `package.json` (scripts, framework), `requirements.txt` or `pyproject.toml`, `go.mod`, `Gemfile`, `pom.xml` or
  `build.gradle`, `Procfile`, and any README run instructions.
- **Monorepos.** With several apps (for example `apps/web` and `apps/api`, or separate service folders), ask which
  app or apps to deploy before going on.
- **Dockerfiles.** Reuse every existing `Dockerfile` and its build context. Write a new one only for a part that has
  none, and keep it minimal: the official base image for the language, install dependencies, copy the source, start
  the app.
- **Ports.** The port each part listens on (from its start script, config or framework default).
- **Backing services.** Databases, caches and queues the code uses, from its dependencies and config (for example
  `pg` or `psycopg` means Postgres, `redis` or `ioredis` means Redis).
- **Variables.** Names from `.env.example`, `.env.sample`, config files and code (`process.env.X`, `os.environ["X"]`).
  Read names only: never read or copy values from a real `.env`.

## 3. Write the file

Write `compose.yml` at the repo root:

- One service per part that runs, with `build` (or `image` for backing services).
- `ports` or `expose` on every service that serves traffic, as a list (`ports: ['3000']`).
- Official images for backing services, pinned to a major version (`postgres:16`, `redis:7`), with their data on a
  named volume.
- `depends_on` from each app service to the backing services it uses.
- Service-to-service URLs use the service name as the host (`postgres://app:app@postgres:5432/app`), never
  `localhost`.

### Shipyard labels

Use only these unless the user asks for more:

| Label | Use |
|---|---|
| `shipyard.route: '/'` | On the service users open first, usually the frontend. Shipyard sends requests with this path prefix to the service's first port. |
| `shipyard.route: '/api'` | On an API that the frontend calls on the same domain. Make sure the API serves under that prefix. |
| `shipyard.primary-route: true` | On the service the dashboard's Visit button should open, when more than one service has a route. |
| `shipyard.init: '<command>'` | A command that must run before the service starts, such as database migrations. Only when the repo clearly has one. |
| `shipyard.readiness.http.path: /healthz` | Only when the app already has a health endpoint. |

Every app needs at least one service with a route, or there's nothing to open.

### Variables

- **Runtime variables** go in `environment`, as `NAME: ${NAME}` for anything the user sets in Shipyard. Give a
  literal value only when it's safe to commit (a port, a feature flag, the backing service's local password).
- **Build args** are variables the build needs, such as `NEXT_PUBLIC_*`, `VITE_*` or `REACT_APP_*`, which frontends
  bake in at build time. Put them under `build.args` as `NAME: ${NAME}`, and make sure the Dockerfile declares
  `ARG NAME`. A build arg set only in `environment` is empty during the build.
- **Secrets** (API keys, tokens, passwords for outside services) never get a value in the file. `plan_application`
  lists their names, and the user gives values at the confirm step or sets them later in the Shipyard dashboard.
- Don't use `env_file` pointing at a file that isn't committed: the build won't have it.

## 4. Check it locally

1. `docker compose config` must succeed. Fix any error it reports.
2. If Docker is running, ask before starting containers, then run `docker compose up --build -d` and request each
   routed service's port. Stop them afterwards with `docker compose down`.
3. If Docker isn't available, say the local check was skipped.

## 5. Problems in a file that works locally

These pass `docker compose up` on a laptop but break on Shipyard. Point each one out and propose a fix:

| Problem | Why | Fix |
|---|---|---|
| Source bind mounts (`./src:/app/src`) | Shipyard ignores bind mounts; only named volumes are kept | Make sure the Dockerfile copies the source in. The mount can stay for local use. |
| `network_mode: host`, or `localhost` URLs between services | Each service is its own host on Shipyard | Use the service name as the host. |
| `env_file` pointing at an untracked file | The file isn't in the repo Shipyard builds | Move the names into `environment` as `${NAME}`. |
| No `ports` or `expose` on a routed service | A route needs a port | Add the port the app listens on. |
| No `shipyard.route` anywhere | Nothing to open | Add one, as in section 3. |
| Private base image | Shipyard can't pull it without credentials | Name the registry and send the user to the Shipyard dashboard to add pull credentials. Never put credentials in the file. |
| `profiles` on services | Services with a profile are off by default in the plan | Ask which to turn on, and pass their profiles as `selected_profiles`. |

## 6. Commit, push, plan

1. Show the user the full file (and any new Dockerfile) and wait for a yes.
2. Ask which branch. Offer a new branch (for example `add-shipyard-compose`) if they don't want it on their main
   branch yet, and tell them the environment follows that branch until they merge.
3. Commit, then ask before pushing. Never push without a yes.
4. Run the preflight again, then call `plan_application`.
