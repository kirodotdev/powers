# Backend Implementation

Context and routing for the `amplify-backend-implementation` Agent SOP.

## When to Use This Workflow

Use this workflow when:
- Setting up user authentication (Cognito)
- Creating data models with GraphQL (AppSync + DynamoDB)
- Adding file storage (S3)
- Implementing serverless functions (Lambda)
- Integrating AI/ML features (Bedrock)

## Retrieve the SOP

```
Tool: retrieve_agent_sop
Parameters: { "sop_name": "amplify-backend-implementation" }
```

The SOP provides comprehensive step-by-step guidance. This steering file provides supplementary context.

## Backend Features Overview

### Authentication (Auth)
- **AWS Services:** Amazon Cognito
- **Features:** Email/password, social providers, MFA, passwordless, user groups
- **Key file:** `amplify/auth/resource.ts`

### Data Layer (Data)
- **AWS Services:** AWS AppSync (GraphQL), Amazon DynamoDB
- **Features:** Real-time subscriptions, authorization rules, relationships
- **Key file:** `amplify/data/resource.ts`

### File Storage (Storage)
- **AWS Services:** Amazon S3
- **Features:** Access levels (guest, authenticated, owner), file triggers
- **Key file:** `amplify/storage/resource.ts`

### Serverless Functions (Functions)
- **AWS Services:** AWS Lambda
- **Features:** Event triggers, environment variables, resource access grants
- **Key directory:** `amplify/functions/`

### AI Features
- **AWS Services:** Amazon Bedrock
- **Features:** Text generation, summarization, conversation routes
- **Requires:** Bedrock model access in target region

## Framework-Agnostic Backend

The backend configuration works with all supported frontend frameworks. The `amplify_outputs.json` file is generated after deployment and contains connection details for your frontend.

## Common Patterns

### Owner-based Authorization
```typescript
// Users can only access their own data
.authorization(allow => [allow.owner()])
```

### Public Read, Authenticated Write
```typescript
.authorization(allow => [
  allow.guest().to(['read']),
  allow.authenticated().to(['create', 'update', 'delete'])
])
```

### Group-based Access
```typescript
.authorization(allow => [
  allow.group('admins').to(['create', 'read', 'update', 'delete']),
  allow.authenticated().to(['read'])
])
```

## Next Steps

After setting up backend:
1. Deploy to sandbox: `npx ampx sandbox`
2. Integrate frontend: Use `amplify-frontend-integration` SOP
3. Deploy to production: Use `amplify-deployment-guide` SOP
