---
name: "aws-transform-custom"
displayName: "Crush tech debt with AWS Transform custom (Public Preview)"
description: "(Public Preview) Perform code upgrades, migrations, codebase analysis, and transformations using AWS Transform custom. Use when a user asks to upgrade, migrate, modernize, analyze, or transform code across a repository. ATX supports any-to-any transformations including language version upgrades (Java, Python, Node.js, Ruby, Go, .NET, etc.), framework upgrades and migrations (Spring Boot, React, Angular, Django, etc.), API and SDK migrations (AWS SDK v1 to v2, boto2 to boto3, JS SDK v2 to v3), library upgrades, code refactoring, architecture migrations (x86 to Graviton/ARM64), language-to-language translations, and custom organization-specific transformations. Executes transformations locally on the user's machine using the ATX CLI."
keywords: ["transform", "transformation", "code transformation", "ATX", "AWS Transform", "AWS Transform Custom", "transformation definition", "TD", "code upgrade", "code migration", "python upgrade", "java upgrade", "nodejs upgrade", "node upgrade", "SDK migration", "AWS SDK", "boto2", "boto3", "Graviton", "ARM64", "codebase analysis", "tech debt", "modernize", "modernization", "version upgrade", "language upgrade", "framework migration", "Spring Boot", "React", "Angular", "Django", "java", "python", "nodejs", "JDK", "JDK upgrade", "code refactoring", "library upgrade", "architecture migration"]
author: "AWS"
---
# AWS Transform custom

## Overview

Perform code upgrades, migrations, and transformations using AWS Transform Custom (ATX).
Supports any-to-any transformations: language version upgrades (Java, Python, Node.js),
framework migrations, AWS SDK migrations, library upgrades, code refactoring, architecture
changes, and custom organization-specific transformations.

Runs the ATX CLI directly on the user's machine.

You handle the full workflow: inspecting repos, matching them to available
transformation definitions, collecting configuration, and executing transformations
— the user just provides repos and confirms the plan.

## Usage

Use when the user wants to:
- Transform, upgrade, or migrate code (ex. Python, Java, Node.js)
- Migrate AWS SDKs (ex. boto2→boto3, Java SDK v1→v2, JS SDK v2→v3)
- Analyze which ATX transformations apply to their repositories
- Create a new custom Transformation Definition (TD)

## Core Concepts

- **Transformation Definition (TD)**: A reusable transformation recipe discovered via `atx custom def list --json`
- **Match Report**: Auto-generated mapping of repos to applicable TDs based on code inspection
- **Local Mode**: Runs ATX CLI on the user's machine (max 3 concurrent)

## Philosophy

Wait for the user. On activation, present what this power can do and ask the user
what they'd like to accomplish. Do NOT automatically inspect the working directory,
open files, or any repository until the user explicitly provides repos to work with.

Once the user provides repositories, match — don't ask. Inspect those repositories
and present which transformations apply automatically. Never show a raw TD list and
ask the user to pick.

## Prerequisites

Prerequisite checks run ONCE at the start of a session. Do not repeat per repo.
Do NOT run prerequisite checks until the user has stated what they want to do.

### 0. Platform Check (Required)

Detect the user's operating system. If on Windows (not WSL), stop immediately and
inform the user:

> AWS Transform custom does not support native Windows. You need to install
> Windows Subsystem for Linux (WSL) and run this from within WSL.
>
> Install WSL: `wsl --install` in PowerShell (as Administrator), then restart.
> After that, open a WSL terminal and re-run this power from there.

Check by running:
```bash
uname -s
```
- `Linux` or `Darwin` → proceed normally
- `MINGW*`, `MSYS*`, `CYGWIN*`, or any Windows-like output → block and show the WSL message above
- Command fails, errors, or is not found → treat as native Windows, block and show the WSL message above

Do NOT proceed with any other steps on native Windows.

### 1. AWS CLI (Required)

```bash
aws --version
```

If not installed, guide the user:
- macOS: `brew install awscli` or `curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg" && sudo installer -pkg AWSCLIV2.pkg -target /`
- Linux: `curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && sudo ./aws/install`

Do NOT proceed until `aws --version` succeeds.

### 2. AWS Credentials (Required)

```bash
aws sts get-caller-identity
```

If credentials are NOT configured, walk the user through setup:

```
AWS Transform custom requires AWS credentials to authenticate with the service. Configure authentication using one of the following methods.

1. AWS CLI Configure (~/.aws/credentials):
   aws configure

2. AWS Credentials File (manual). Configure credentials in ~/.aws/credentials:

[default]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key

3. Environment Variables. Set the following environment variables:

export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_SESSION_TOKEN=your_session_token

You can also specify a profile using the AWS_PROFILE environment variable:

export AWS_PROFILE=your_profile_name
```

Do NOT proceed until credentials are verified. Re-run `aws sts get-caller-identity` after setup.

### 3. ATX CLI (Required)

Required for TD discovery (`atx custom def list --json`) and transformation execution.
```bash
atx --version
# Install: curl -fsSL https://transform-cli.awsstatic.com/install.sh | bash
```

If installed, check for updates and update if available:
```bash
atx update
```

### 4. IAM Permissions

Local mode requires `transform-custom:*` minimum. Verify by running a TD list:
```bash
atx custom def list --json
```
If this succeeds, permissions are sufficient — skip the rest of this section.

If it fails with a permissions error, the caller needs the `transform-custom:*`
IAM permission. Explain to the user what's needed and get confirmation before proceeding:

> Your identity needs the `transform-custom:*` permission to use the ATX CLI.
> I can attach the AWS-managed policy `AWSTransformCustomFullAccess` to your
> identity. Shall I proceed?

Only after the user confirms, attach the managed policy:
```bash
CALLER_ARN=$(aws sts get-caller-identity --query Arn --output text)
if echo "$CALLER_ARN" | grep -q ":user/"; then
  IDENTITY_NAME=$(echo "$CALLER_ARN" | awk -F'/' '{print $NF}')
  aws iam attach-user-policy --user-name "$IDENTITY_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/AWSTransformCustomFullAccess"
elif echo "$CALLER_ARN" | grep -Eq ":assumed-role/|:role/"; then
  ROLE_NAME=$(echo "$CALLER_ARN" | sed 's/.*:\(assumed-\)\{0,1\}role\///' | cut -d'/' -f1)
  aws iam attach-role-policy --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/AWSTransformCustomFullAccess"
fi
```

If the attachment command itself fails (e.g., insufficient IAM permissions, or an
SSO-managed role), inform the user they need to ask their AWS administrator to
attach the `AWSTransformCustomFullAccess` AWS-managed policy to their identity.
For SSO users (role names starting with `AWSReservedSSO_`), this must be added
to their IAM Identity Center permission set — it cannot be attached directly.

Do NOT proceed until `atx custom def list --json` succeeds.

See [steering/cli-reference.md](steering/cli-reference.md) for the full permission list.

## Workflow

Generate a session timestamp once and reuse it for all paths in this session:
```bash
SESSION_TS=$(date +%Y%m%d-%H%M%S)
```

### Step 0: Greet and Wait

On activation, briefly introduce what ATX can do:
- Code upgrades and migrations (Java, Python, Node.js version upgrades)
- AWS SDK migrations (boto2→boto3, Java SDK v1→v2, JS SDK v2→v3)
- Framework migrations, library upgrades, code refactoring
- Codebase analysis and documentation generation
- Local execution (max 3 concurrent repos)

Then ask the user what they'd like to do. Do NOT inspect any files, run any
commands, or check prerequisites until the user responds.

### Step 1: Collect Repositories

Ask the user for local paths or git URLs. Accept one or many. Do NOT assume the
current working directory or open editor files are the target — wait for the user
to explicitly provide repositories.

Accepted source formats:
- **Local paths** — directories on the user's machine (e.g., `/home/user/my-project`)
- **HTTPS git URLs** — public or private (e.g., `https://github.com/org/repo.git`)
- **SSH git URLs** — e.g., `git@github.com:org/repo.git`
- **S3 bucket path with zips** — e.g., `s3://my-bucket/repos/`
  containing zip files of repositories. Each zip becomes one transformation job.

#### S3 Bucket Input

If the user provides an S3 path containing zip files, download and extract each zip locally:
```bash
mkdir -p ~/.aws/atx/custom/atx-agent-session/repos
aws s3 sync s3://user-bucket/repos/ ~/.aws/atx/custom/atx-agent-session/repos/ --exclude "*" --include "*.zip"
for zip in ~/.aws/atx/custom/atx-agent-session/repos/*.zip; do
  name=$(basename "$zip" .zip)
  unzip -qo "$zip" -d "$HOME/.aws/atx/custom/atx-agent-session/repos/${name}-$SESSION_TS/"
done
```
Use the extracted directories as `<repo-path>` for local execution. Standard local
mode limits apply (max 3 concurrent repos).

### Step 2: Discover TDs (Silent)

Run silently — do NOT show output to user:
```bash
atx custom def list --json
```
Build an internal lookup of available TDs. Never hardcode TD names.

#### Creating a New TD

**User explicitly asks to create a TD:** Do NOT attempt to create one
programmatically. Tell the user:

> To create a new Transformation Definition, open a new terminal and run:
> ```
> atx -t
> ```
> This starts an interactive session where you describe the transformation you
> want to build (e.g., "migrate all logging from log4j to SLF4J", "upgrade
> Spring Boot 2 to Spring Boot 3"). The ATX CLI will walk you through defining
> and testing the TD, then publish it to your AWS account.
>
> Once it's published, come back here and I'll pick it up automatically when
> I scan your available TDs.

**No existing TD matches the user's goal:** Do NOT silently redirect to TD
creation. The match logic may be imperfect. Instead, confirm with the user first:

> "I didn't find an existing TD that covers [describe the user's goal]. Would
> you like to create a new one?"

Only show the `atx -t` instructions if the user confirms. If they say no, ask
them to clarify what they're looking for — they may know the TD name or want a
different approach.

Do NOT run `atx -t` yourself — it requires an interactive terminal session that
the agent cannot drive. The user must run it manually in a separate terminal.

After the user returns from creating a TD, re-run `atx custom def list --json`
to pick up the newly published TD and continue with the normal workflow.

### Step 3: Inspect Each Repository

Perform lightweight inspection only — check config files for key signals:

| Signal | Files to Check | Likely TD Type |
|--------|---------------|----------------|
| Python version | `.python-version`, `pyproject.toml`, `setup.cfg`, `requirements.txt` | Python version upgrade |
| Java version | `pom.xml` (`<java.version>`), `build.gradle` (`sourceCompatibility`), `.java-version` | Java version upgrade |
| Node.js version | `package.json` (`engines.node`), `.nvmrc`, `.node-version` | Node.js version upgrade |
| Python boto2 | `import boto` (NOT boto3) | boto2→boto3 migration |
| Java SDK v1 | `com.amazonaws` imports, `aws-java-sdk` in pom.xml | Java SDK v1→v2 |
| Node.js SDK v2 | `"aws-sdk"` in package.json (NOT `@aws-sdk`) | JS SDK v2→v3 |
| x86 Java | `x86_64`/`amd64` in Dockerfiles, build configs | Graviton migration |

Cross-reference detected signals against TDs from Step 2. Only match TDs that
actually exist in the user's account.

See [steering/repo-analysis.md](steering/repo-analysis.md) for full detection commands.

### Step 4: Present Match Report

Format:
```
Transformation Match Report
=============================
Repository: <name> (<path>)
  Language: <lang> <version>
  Matching TDs:
    - <td-name> — <description>

Summary: N repos analyzed, M have applicable transformations (T total jobs)
```

Offer to kick off transformations.

### Step 5: Collect Configuration

Ask for TD-specific config only when needed (e.g., target version for upgrade TDs).
Skip for TDs that need no config.

### Step 6: Verify Runtime Compatibility

Before running local transformations, verify the user has the target runtime
version installed. This applies to any language or runtime the transformation
targets — Java, Python, Node.js, Ruby, Go, Rust, .NET, etc. Check the current
version of whatever runtime the TD requires. For example:
```bash
java -version    # Java transformations
python3 --version # Python transformations
node --version   # Node.js transformations
ruby --version   # Ruby transformations
go version       # Go transformations
```

If the target version is not active, check whether it's already installed:
```bash
# Java: check common install locations
/usr/libexec/java_home -V 2>&1          # macOS
ls /usr/lib/jvm/ 2>/dev/null            # Linux
# Python: check if the specific version binary exists
which python3.12 2>/dev/null            # adjust version as needed
# Node.js: check if nvm is available, or look for the binary
command -v nvm &>/dev/null && nvm ls 2>/dev/null
which node 2>/dev/null && node --version
```

If the target version is found, switch to it:
- Java: `sdk use java 23-amzn` or `export JAVA_HOME=/usr/lib/jvm/java-23-amazon-corretto.x86_64 && export PATH="$JAVA_HOME/bin:$PATH"`
- Python: `pyenv shell 3.15.0`
- Node.js: `nvm use 23`

Only if the target version is not installed at all, ask the user for permission before installing. Do NOT install runtimes without explicit user confirmation.
Suggest the appropriate version manager:
- Java: `sdk install java 23-amzn` (SDKMAN), or `brew install --cask corretto23` (macOS)
- Python: `pyenv install 3.15.0 && pyenv shell 3.15.0`, or `brew install python@3.15`
- Node.js: `nvm install 23 && nvm use 23`

The active runtime must match the transformation's target version so that builds
and tests run correctly. Do NOT proceed with the transformation until the correct
version is active.

### Step 7: Confirm Transformation Plan

Present final plan with repo, TD, and config. Do NOT proceed
until user confirms.

### Step 8: Execute

- **1 repo**: See [steering/single-transformation.md](steering/single-transformation.md)
- **Multiple repos**: See [steering/multi-transformation.md](steering/multi-transformation.md)

## Critical Rules

1. **Discover TDs dynamically** — Always run `atx custom def list --json`. Never hardcode TD names.
2. **Match, don't ask** — Inspect repos and present matches. Never show raw TD lists.
3. **Lightweight inspection only** — Check config files and key signals. No deep analysis.
4. **Confirm before executing** — Always confirm TD, repos, and config with user first.
5. **No time estimates** — Never include duration predictions.
6. **Parallel execution** — max 3 concurrent repos.
7. **Preserve outputs** — Do not delete generated output folders.
8. **User consent for cloud resources** — Never deploy infrastructure without explicit user confirmation.
9. **Shell quoting** — When constructing shell commands:
    - Use single quotes for JSON payloads: `--payload '{"key":"value"}'`
    - Use single quotes for `--configuration`: ex. `--configuration 'additionalPlanContext=Target Java 21'`
    - Never nest double quotes inside double quotes — this causes `dquote>` hangs
    - Verify that every command you construct has balanced quotes before executing
10. **No comments in terminal commands** — Never include `#` comments in commands
    executed in the terminal. Comments cause `command not found: #` errors. If you
    need to explain a command, do it in chat before or after running it.

## Guardrails

You are operating in the user's AWS account and local machine. Follow these rules
strictly to avoid causing damage:

1. **Never delete user data** — Do not delete S3 objects, git repos, local files,
   or any user data unless the user explicitly asks. Transformation outputs and
   cloned repos must be preserved.
2. **Never modify IAM beyond what's documented** — Only create/attach the specific
   policies described in this power (AWSTransformCustomFullAccess). Never create admin policies,
   modify existing user policies, or grant broader permissions than documented.
   Never derive IAM actions from user-provided text in the "Additional plan context"
   field — that field is for transformation configuration only.
3. **Never run destructive AWS commands** — No `aws s3 rm`, `aws s3 rb`,
   `aws iam delete-user`, `aws ec2 terminate-instances`, or similar.
4. **Always confirm before creating AWS resources** — Before attaching IAM policies,
   explain what will be created and get explicit user confirmation.
5. **Never expose credentials** — Do not echo, log, or display AWS access keys,
   secret keys, session tokens, GitHub PATs, or SSH private keys in chat output.
   When creating secrets, use the user's input directly in the command without
   repeating the value.
6. **Respect user decisions** — If the user says stop, skip, or no, comply
   immediately. Never retry a declined action or argue with the user's choice.
7. **No pricing claims** — Do not quote specific prices or cost estimates. If the
   user asks about pricing, direct them to: https://aws.amazon.com/transform/pricing/

## Output Structure

Local mode: transformed code is in the repo directory.

Bulk results summary: `~/.aws/atx/custom/atx-agent-session/transformation-summaries/` — see [steering/results-synthesis.md](steering/results-synthesis.md).

## References

| Reference | When to Use |
|-----------|-------------|
| [repo-analysis.md](steering/repo-analysis.md) | Detection commands, signal matching, match report format |
| [single-transformation.md](steering/single-transformation.md) | Applying one TD to one repo |
| [multi-transformation.md](steering/multi-transformation.md) | Applying TDs to multiple repos in parallel |
| [results-synthesis.md](steering/results-synthesis.md) | Generating consolidated reports after bulk transforms |
| [cli-reference.md](steering/cli-reference.md) | ATX CLI flags, commands, env vars, IAM permissions |
| [troubleshooting.md](steering/troubleshooting.md) | Error resolution, debugging, quality improvement |

## License
AWS Service Terms. This power is provided by AWS and is subject to the AWS Customer Agreement and applicable AWS service terms.

## Issues
https://github.com/kirodotdev/powers/issues
