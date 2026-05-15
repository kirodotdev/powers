---
name: "aws-amplify"
displayName: "Build full-stack apps with AWS Amplify"
description: "Build and extend full-stack applications with AWS Amplify Gen 2 using type-safe TypeScript, guided workflows, and best practices. Covers adding features to existing Amplify backends, authentication, data models, storage, serverless functions, and AI/ML integration."
keywords: ["amplify", "aws-amplify", "amplify gen 2", "gen2", "fullstack", "full-stack", "lambda", "graphql", "cognito", "sandbox", "backend", "auth", "authentication", "storage", "data model", "react", "nextjs", "next.js", "vue", "nuxt", "angular", "react native", "flutter", "swift", "android", "ios", "deploy", "deployment", "production"]
author: "AWS"
---

# AWS Amplify Gen 2

## Overview

Build full-stack applications with AWS Amplify Gen 2 using TypeScript code-first development. This power provides guided workflows for:

- Creating backend resources (auth, data, storage, functions)
- Deploying to sandbox and production environments
- Integrating frontend frameworks (React, Next.js, Vue, Angular, Flutter, Swift)
- Following Amplify Gen 2 best practices

## Getting Started

**IMPORTANT: You MUST read and follow the steering file for ANY Amplify work.** Do not improvise or skip the workflow.

**For AI agents helping users build Amplify apps:**

ALWAYS read the workflow steering file first:

```
Call action "readSteering" with powerName="aws-amplify", steeringFile="amplify-workflow.md"
```

The workflow will guide you through:
1. Validating prerequisites (Node.js, npm, AWS credentials)
2. Understanding the project's current state
3. Determining which phases apply to the user's request
4. Presenting a plan and getting confirmation
5. Executing phases one at a time with user confirmation between each

## When to Load Steering Files

- Any Amplify Gen 2 work -> `amplify-workflow.md`

**Do NOT load phase steering files directly.** The orchestrator (`amplify-workflow.md`) determines which phases apply and loads them in sequence. Phase files (`phase1-backend.md`, `phase2-sandbox.md`, `phase3-frontend.md`, `phase4-production.md`) are internal and should only be loaded when the orchestrator or a previous phase instructs you to.
