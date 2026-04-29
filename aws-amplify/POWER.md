---
name: aws-amplify
displayName: Build full-stack apps with AWS Amplify Gen2
description: 'Build and deploy full-stack web and mobile apps with AWS Amplify Gen2
  (TypeScript code-first). Covers auth (Cognito), data (AppSync/DynamoDB including
  schema modeling, enum types, relationships, authorization rules), storage (S3),
  functions, APIs, and AI (Amplify AI Kit with Bedrock). Supports React, Next.js,
  Vue, Angular, React Native, Flutter, Swift, and Android. Always use this skill for
  Amplify Gen2 topics — even for questions you think you know — it contains validated,
  version-specific patterns that prevent common mistakes. TRIGGER when: user mentions
  Amplify Gen2; project has amplify/ directory or amplify_outputs; code imports @aws-amplify
  packages; user asks about defineBackend, defineAuth, defineData, defineStorage,
  or npx ampx. SKIP: Amplify Gen1 (amplify CLI v6), standalone SAM/CDK without Amplify
  (use aws-serverless), direct Bedrock without Amplify AI Kit (use bedrock).

  '
keywords:
- amplify
- gen2
- fullstack
- cognito
- appsync
- dynamodb
- s3
- lambda
- bedrock
- react
- nextjs
- flutter
- swift
- android
author: AWS
---

# AWS Amplify Gen2

## Overview

AWS Amplify Gen2 is a TypeScript code-first developer experience for building full-stack web and mobile applications. All backend resources — authentication (Cognito), data (AppSync/DynamoDB), storage (S3), serverless functions (Lambda), and AI (Bedrock via Amplify AI Kit) — are defined in TypeScript under an `amplify/` directory. A single `amplify_outputs.json` file is generated to configure frontends.

**Supported frameworks:** React (Vite), Next.js, Vue, Angular, React Native, Flutter, Swift, Android.

**Key differences from Gen1:** No CLI wizards, no `amplify push` — everything is code-defined and deployed via `npx ampx sandbox` (dev) or `npx ampx pipeline-deploy` (CI/CD).

## Getting Started

### Prerequisites

- Node.js ^18.19.0 || ^20.6.0 || >=22 and npm
- AWS credentials configured (`aws sts get-caller-identity` succeeds)
- For sandbox: `npx ampx --version` returns a valid version
- For mobile: Platform-specific tooling (Xcode, Android Studio, Flutter SDK)

### Quick Start

```bash
# Create a new Amplify Gen2 project
npm create amplify@latest

# Start local sandbox (watches for changes, hot-deploys to AWS)
npx ampx sandbox
```

### Project Structure

```
project-root/
├── amplify/
│   ├── backend.ts            # defineBackend({ auth, data, ... })
│   ├── auth/resource.ts      # defineAuth({ ... })
│   ├── data/resource.ts      # defineData({ schema })
│   ├── storage/resource.ts   # defineStorage({ ... })
│   └── functions/
│       └── my-func/
│           ├── resource.ts   # defineFunction({ ... })
│           └── handler.ts    # export const handler = ...
├── src/                      # Frontend code
├── amplify_outputs.json      # Generated — DO NOT edit or commit
└── package.json
```

### Key Packages

| Package | Purpose |
|---------|---------|
| `@aws-amplify/backend` | `defineAuth`, `defineData`, `defineStorage`, `defineFunction`, `defineBackend` |
| `aws-amplify` | Frontend: `Amplify.configure()`, `generateClient()`, auth/data/storage APIs |
| `@aws-amplify/ui-react` | Pre-built UI: `<Authenticator>`, `<StorageBrowser>` |
| `@aws-amplify/ui-react-ai` | AI UI: `<AIConversation>`, `useAIConversation` |

## When to Load Steering Files

**IMPORTANT:** Always load the appropriate steering file(s) before starting any Amplify work. Do not improvise — these files contain validated, version-specific patterns.

### Step 0: Always Load the Core Reference First

Before reading any feature-specific steering file, you **MUST** load the core reference for your target platform. These contain Gen2 detection, `Amplify.configure()` placement per framework, sandbox commands, required packages, and directory structure rules.

| Platform | Steering File | When |
|----------|---------------|------|
| Web (React, Next.js, Vue, Angular, React Native) | `core-web.md` | Any web/RN frontend work |
| Mobile (Flutter, Swift, Android) | `core-mobile.md` | Any native mobile frontend work |
| Backend only (no frontend) | Skip to Step 1 | No frontend changes needed |

### Step 1: Project Scaffolding

| Task | Steering File |
|------|---------------|
| Create a new Amplify Gen2 project | `scaffolding.md` → then continue to Step 2 and/or Step 3 |

### Step 2: Backend Features

Load the steering file for each backend feature you need to add or modify:

| Feature | Steering File | Covers |
|---------|---------------|--------|
| Authentication | `auth-backend.md` | Email/password, social login, MFA, SAML/OIDC, user groups, custom attributes |
| Data Models | `data-backend.md` | GraphQL schema, DynamoDB, relationships, enum types, authorization rules |
| File Storage | `storage-backend.md` | S3 buckets, access rules (guest/authenticated/groups/entity), paths |
| Functions & APIs | `functions-and-api.md` | Lambda functions, custom resolvers, REST/HTTP APIs, environment variables |
| AI Features | `ai.md` | Conversation routes, generation routes, AI tools via Bedrock (backend + React/Next.js frontend) |
| Geo, PubSub, CDK | `advanced-features.md` | Custom CDK stacks, overrides, custom outputs, Geo, PubSub, Face Liveness |

### Step 3: Frontend Integration

After configuring backend resources, load the frontend steering file for your platform and feature:

**Web** (React, Next.js, Vue, Angular, React Native):

| Feature | Steering File |
|---------|---------------|
| Auth UI & flows | `auth-web.md` |
| Data CRUD & subscriptions | `data-web.md` |
| Storage upload/download | `storage-web.md` |

**Mobile** (Flutter, Swift, Android):

| Feature | Steering File |
|---------|---------------|
| Auth UI & flows | `auth-mobile.md` |
| Data CRUD & subscriptions | `data-mobile.md` |
| Storage upload/download | `storage-mobile.md` |

> **Note:** AI and Functions frontend patterns are included in `ai.md` and `functions-and-api.md` respectively — they are not split into separate web/mobile files.

### Step 4: Deployment

| Task | Steering File |
|------|---------------|
| Deploy to sandbox or production | `deployment.md` |

### Quick Routing Examples

| User Says | Load |
|-----------|------|
| "Build a full-stack app" | `core-web.md` → `scaffolding.md` → backend files → frontend files → `deployment.md` |
| "Add authentication" | `auth-backend.md` (+ `core-web.md` → `auth-web.md` if frontend needed) |
| "Add a data model" | `data-backend.md` |
| "Connect my React app to Amplify" | `core-web.md` → relevant frontend files |
| "Deploy to production" | `deployment.md` |
| "Add AI chat" | `ai.md` (includes both backend and React/Next.js frontend) |
| "Build a Flutter app with auth" | `core-mobile.md` → `scaffolding.md` → `auth-backend.md` → `auth-mobile.md` |

## Available MCP Tools

When AWS documentation MCP tools are available, use them to look up advanced CDK constructs, service limits, or provider-specific configuration.

| Tool | Use For |
|------|---------|
| `search_documentation` | Find Amplify Gen2 documentation pages by topic |
| `read_documentation` | Read specific Amplify documentation pages |
| `recommend` | Get related documentation recommendations |

**Tip:** Amplify's LLM-optimized docs are at [https://docs.amplify.aws/ai/llms.txt](https://docs.amplify.aws/ai/llms.txt)

## Common Workflows

### 1. Scaffold a New Full-Stack Project

```bash
npm create amplify@latest
cd my-amplify-app
npx ampx sandbox
```

Load `scaffolding.md` for framework-specific setup, directory structure, and starter template details.

### 2. Add Authentication

In `amplify/auth/resource.ts`:
```typescript
import { defineAuth } from '@aws-amplify/backend';

export const auth = defineAuth({
  loginWith: {
    email: true, // or phone, or external providers
  },
});
```

Register in `amplify/backend.ts`:
```typescript
import { defineBackend } from '@aws-amplify/backend';
import { auth } from './auth/resource';

defineBackend({ auth });
```

Load `auth-backend.md` for MFA, social login, SAML/OIDC, custom attributes, and user groups.

### 3. Add a Data Model

In `amplify/data/resource.ts`:
```typescript
import { type ClientSchema, a, defineData } from '@aws-amplify/backend';

const schema = a.schema({
  Todo: a.model({
    content: a.string(),
    isDone: a.boolean(),
  }).authorization(allow => [allow.publicApiKey()]),
});

export type Schema = ClientSchema<typeof schema>;
export const data = defineData({ schema });
```

Load `data-backend.md` for relationships, enum types, secondary indexes, and authorization rules.

### 4. Deploy to Production

```bash
# CI/CD pipeline deployment
npx ampx pipeline-deploy --branch main --app-id <amplify-app-id>
```

Load `deployment.md` for Amplify Hosting, custom CI/CD pipelines, environment management, and fullstack branch deployments.

## Defaults & Assumptions

When the user does not specify preferences:

| Choice | Default | Notes |
|--------|---------|-------|
| Web framework | React (Vite) | Explain the choice; user can override |
| Mobile framework | **ASK** | No default — must ask Flutter/Swift/Android/RN |
| Package manager | npm | Unless user specifies yarn or pnpm |
| Language | TypeScript | Gen2 backends are TS-only; frontends follow project convention |
| Next.js router | App Router | Unless user specifies Pages Router |
| Auth login method | Email/password | Unless user specifies social/SAML/other |
| Data authorization | `publicApiKey` | Switch to `owner`-based when auth is added |

**Critical:** If the user says "build an app" without specifying web vs. mobile, you **MUST** ask before proceeding.

## Best Practices

1. **Always use the `amplify/` directory** — all backend resources are TypeScript files under `amplify/`. Never use CLI wizards or manual AWS console configuration.

2. **Never edit `amplify_outputs.json`** — this file is auto-generated by `npx ampx sandbox` (dev) or `npx ampx pipeline-deploy` (CI/CD). It should be in `.gitignore`.

3. **One `defineBackend()` call** — in `amplify/backend.ts`, combine all resources into a single `defineBackend({ auth, data, storage })` call.

4. **Use `a.schema()` for data models** — define your GraphQL schema using the type-safe `a` builder from `@aws-amplify/backend`. Avoid writing raw GraphQL SDL.

5. **Authorization rules are mandatory** — every model needs `.authorization(allow => [...])`. Start with `allow.publicApiKey()` for prototyping, switch to `allow.owner()` or `allow.groups()` for production.

6. **Configure Amplify once at the app root** — call `Amplify.configure(outputs)` in your root layout/entry file, never in individual components.

7. **Use pre-built UI components** — `<Authenticator>` from `@aws-amplify/ui-react` handles the entire auth flow. Don't build custom login forms unless you have specific requirements.

8. **Sandbox for development** — `npx ampx sandbox` creates an isolated cloud environment per developer. Use `--identifier` for multiple sandboxes.

## Troubleshooting

### Sandbox Won't Start

**Symptoms:** `npx ampx sandbox` fails with credential or bootstrap errors.

**Solutions:**
1. Verify AWS credentials: `aws sts get-caller-identity`
2. Bootstrap CDK if first time: `npx ampx sandbox` will prompt automatically
3. Check Node.js version: must be ^18.19.0, ^20.6.0, or >=22
4. Ensure no other sandbox is running with the same identifier

### "Cannot find module" or Import Errors

**Cause:** Missing dependencies or incorrect import paths.

**Solutions:**
1. Run `npm install` to ensure all packages are installed
2. Check that `@aws-amplify/backend` is in `devDependencies` (not `dependencies`)
3. Check that `aws-amplify` is in `dependencies` for frontend code
4. Verify import paths match the package names exactly

### Data Model Authorization Errors

**Symptoms:** "Not Authorized" errors when querying or mutating data.

**Solutions:**
1. Ensure every model has `.authorization(allow => [...])` rules
2. Check `defaultAuthorizationMode` in `defineData()` matches your auth setup
3. For authenticated access, ensure the user is signed in before making API calls
4. For `owner`-based auth, the `owner` field is auto-managed — don't set it manually

### `amplify_outputs.json` Not Found

**Cause:** Sandbox hasn't been started, or the file is gitignored (expected).

**Solutions:**
1. Run `npx ampx sandbox` to generate the file locally
2. For CI/CD, `npx ampx pipeline-deploy` generates it during build
3. Ensure your `.gitignore` includes `amplify_outputs.json` — it should NOT be committed

### Next.js SSR/SSG Issues

**Symptoms:** `Amplify.configure()` errors in server components, hydration mismatches.

**Solutions:**
1. Call `Amplify.configure()` in a client-side wrapper component (`'use client'`)
2. For server-side data access, use `generateServerClientUsingCookies()` from `aws-amplify/adapter-nextjs`
3. Never import `aws-amplify` in server components directly

## Resources

- [Amplify Gen2 Documentation](https://docs.amplify.aws/react/)
- [Amplify Docs for LLMs](https://docs.amplify.aws/ai/llms.txt)
- [Getting Started Guide](https://docs.amplify.aws/react/start/)
- [Quickstart Tutorial](https://docs.amplify.aws/react/start/quickstart/)
- [Account Setup](https://docs.amplify.aws/react/start/account-setup/)
- [How Amplify Works](https://docs.amplify.aws/react/how-amplify-works/)
- [Build a Backend](https://docs.amplify.aws/react/build-a-backend/)
- [Deploy and Host](https://docs.amplify.aws/react/deploy-and-host/)
- [CLI Reference](https://docs.amplify.aws/react/reference/cli-commands/)
- [Project Structure Reference](https://docs.amplify.aws/react/reference/project-structure/)
- [Amplify UI Components](https://ui.docs.amplify.aws/)
- [Amplify GitHub](https://github.com/aws-amplify)

> All documentation links use `react` as the default platform slug. Replace `/react/` with `/nextjs/`, `/vue/`, `/angular/`, `/react-native/`, `/flutter/`, `/swift/`, or `/android/` for other frameworks.

---

This power integrates with [`awslabs.aws-documentation-mcp-server@latest`](https://github.com/awslabs/mcp) for documentation search and retrieval.
