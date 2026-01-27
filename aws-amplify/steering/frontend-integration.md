# Frontend Integration

Context and routing for the `amplify-frontend-integration` Agent SOP.

## When to Use This Workflow

Use this workflow when:
- Adding Amplify to an existing frontend app
- Implementing authentication UI
- Fetching and mutating data
- Setting up real-time subscriptions
- Configuring state management

## Retrieve the SOP

```
Tool: retrieve_agent_sop
Parameters: { "sop_name": "amplify-frontend-integration" }
```

## Framework-Specific Guidance

### React
- Use `@aws-amplify/ui-react` for pre-built components
- Leverage React hooks for auth state (`useAuthenticator`)
- Configure Amplify in `src/main.tsx` or `src/index.tsx`

### Next.js
- Supports both App Router and Pages Router
- Server components require special handling
- Use `runWithAmplifyServerContext` for SSR

### Vue
- Use Composition API with `@aws-amplify/ui-vue`
- Configure in main app entry (`main.ts`)

### Angular
- Use `@aws-amplify/ui-angular`
- Configure in `app.module.ts`
- Implement route guards for protected routes

### React Native
- Use `@aws-amplify/ui-react-native`
- Configure secure storage for tokens
- Handle offline scenarios with DataStore

### Flutter
- Use `amplify_flutter` packages
- Configure in `main.dart`
- Platform-specific setup required (iOS/Android)

### Swift (iOS)
- Use `Amplify` Swift package
- Async/await patterns for all operations
- Configure in `AppDelegate` or `App` struct

### Android (Kotlin)
- Use `com.amplifyframework` packages
- Coroutines for async operations
- Configure in `Application` class

## Common Integration Pattern

```typescript
// 1. Import and configure (do once at app entry)
import { Amplify } from 'aws-amplify';
import outputs from '../amplify_outputs.json';
Amplify.configure(outputs);

// 2. Generate typed client
import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../amplify/data/resource';
const client = generateClient<Schema>();

// 3. Use in components
const { data } = await client.models.Todo.list();
```

## UI Components

Amplify UI provides pre-built, customizable components:

| Component | Purpose |
|-----------|---------|
| `Authenticator` | Complete auth flow UI |
| `StorageImage` | Display S3 images |
| `FileUploader` | Upload files to S3 |
| `AccountSettings` | User profile management |

## Next Steps

After frontend integration:
- Test locally with sandbox: `npx ampx sandbox`
- Deploy: Use `amplify-deployment-guide` SOP
