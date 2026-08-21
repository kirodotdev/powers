# App Code Rules — Mandatory for ANY Application Code Changes

When this Power touches application code (wiring env vars, fixing configs, updating Dockerfiles, patching source for deploy compatibility), these rules apply unconditionally.

---

## 1. File Edits

- **Prefer full-file rewrite.** Read entire file → build new content → write complete file.
- **Never** use byte-offset or character-offset edits. Source may contain multi-byte UTF-8.
- For targeted changes, use **exact string match** replace. If the match is ambiguous or missing — stop, don't guess.
- Do not strip comments, licenses, or unrelated code while editing.
- Touch only the minimum lines needed for the change.

## 2. Config / Environment Wiring

- Change **only** the keys the deploy requires (API URL, DATABASE_URL, env vars). Leave everything else unchanged.
- Do not hardcode environment URLs into application logic. Put them in `.env`, `docker-compose.yml`, or the app's designated config file.
- If the app already has local/deployed URL resolution logic — preserve it. Don't add special-casing.
- Prefer ASCII in auto-generated configs. If existing file uses Unicode, preserve it exactly.

## 3. Validate BEFORE Deploy

After editing any file that will be deployed:

- **JS/TS:** `node --check <file>` or equivalent syntax check
- **JSON:** Parse with `python3 -c "import json; json.load(open('<file>'))"`
- **YAML:** Parse with `python3 -c "import yaml; yaml.safe_load(open('<file>'))"`
- **Dockerfile:** `docker build --check` or at minimum verify no syntax errors
- **HCL/Terraform:** `tofu validate` or `terraform validate`

**If validation fails → ABORT.** Do not upload, apply, or continue. Fix first, then re-validate.

## 4. Validate AFTER Deploy

- Fetch the live URL and confirm it returns expected HTTP status (200, not 502/503/404)
- Check critical endpoints respond (`/`, `/api/health`, etc.)
- If a Lambda or serverless function: invoke it once and confirm no errors in response
- If post-deploy validation fails: fix via IaC (update config → re-Plan → re-Apply), not via direct CLI patches

## 5. Scope Discipline

- Touch ONLY files needed for the deploy/infra outcome.
- Do NOT refactor, rename, reformat, or "clean up" unrelated code.
- Do NOT change application business logic when the task is infrastructure wiring.
- Do NOT commit secrets, tokens, or private keys into source files.
- If a code change is needed for deploy compatibility (e.g., adding a credential provider) — make the minimal change and nothing else.

## 6. Hard Stops (always abort if any of these happen)

- Editing a source file with byte offsets that could corrupt UTF-8
- Uploading a file that fails syntax validation
- Deployed endpoint returns errors and no IaC fix is possible
- Changing application business logic when task was only "deploy to AWS"
