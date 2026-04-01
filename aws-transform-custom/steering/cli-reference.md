# ATX CLI Reference

## Execution Flags (`atx custom def exec`)

| Flag | Long Form | Description |
|------|-----------|-------------|
| `-n` | `--transformation-name <name>` | TD name (from `atx custom def list --json`) |
| `-p` | `--code-repository-path <path>` | Path to code repo (`.` for current dir) |
| `-c` | `--build-command <cmd>` | Build/validation command (optional, auto-detected) |
| `-x` | `--non-interactive` | No user prompts |
| `-t` | `--trust-all-tools` | Auto-approve tool executions (required with `-x`) |
| `-d` | `--do-not-learn` | Prevent knowledge item extraction |
| `-g` | `--configuration <config>` | Config file (`file://config.yaml`) or inline (`'key=val'`) |
| `--tv` | `--transformation-version <ver>` | Specific TD version |

## Build Commands

| Language | Command | Notes |
|----------|---------|-------|
| Java (Maven) | `mvn clean install` | Most common |
| Java (Gradle) | `gradle clean build` | Alternative |
| Python | `pytest` | Or `python -m pytest` |
| Node.js | `npm run build` or `npm test` | Framework-dependent |

`-c` is optional. ATX auto-detects from project files. Include when auto-detection
may fail or a specific command is needed.

Best practices for build commands:
- Use a deterministic, specific command that returns errors on failure
- Even non-compiled languages benefit from linters, test runners, or formatters
- If no building is needed, use `"noop"`
- If the build command is not `"noop"`, verify the command works locally before passing it to ATX

## Configuration

Inline: `--configuration 'additionalPlanContext=Target Python 3.13'`

YAML file:
```yaml
transformationName: AWS/java-version-upgrade
buildCommand: mvn clean install
additionalPlanContext: |
  Target Java 17. Ensure compatibility with internal logging.
```
Usage: `atx custom def exec -g file://config.yaml -x -t`

`--configuration` is optional. Omit if no extra context needed.

## Other Commands

| Action | Command |
|--------|---------|
| Start interactive conversation | `atx` |
| Resume most recent conversation | `atx --resume` |
| Resume specific conversation | `atx --conversation-id <id>` (30-day limit) |
| List TDs | `atx custom def list --json` |
| Download TD | `atx custom def get -n <name>` (optional: `--tv <version>`, `--td <directory>`) |
| Delete TD | `atx custom def delete -n <name>` |
| Save TD as draft | `atx custom def save-draft -n <name> --description "<desc>" --sd <dir>` |
| Publish TD | `atx custom def publish -n <name> --description "<desc>" --sd <dir>` |
| List knowledge items | `atx custom def list-ki -n <name>` |
| View knowledge item | `atx custom def get-ki -n <name> --id <id>` |
| Enable/disable KI | `atx custom def update-ki-status -n <name> --id <id> --status ENABLED or DISABLED` |
| KI auto-approval on/off | `atx custom def update-ki-config -n <name> --auto-enabled TRUE or FALSE` |
| Export KIs | `atx custom def export-ki-markdown -n <name>` |
| Delete KI | `atx custom def delete-ki -n <name> --id <id>` |
| Update CLI | `atx update` |
| Check for CLI updates only | `atx update --check` |
| Tag a TD | `atx custom def tag --arn <arn> --tags '{"key":"value"}'` |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ATX_SHELL_TIMEOUT` | 900 (15 min) | Shell command timeout in seconds |
| `ATX_DISABLE_UPDATE_CHECK` | false | Disable version check |
| `AWS_PROFILE` | — | AWS credentials profile |
| `AWS_ACCESS_KEY_ID` | — | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | — | AWS secret key |
| `AWS_SESSION_TOKEN` | — | Session token (temporary credentials) |

## IAM Permissions

Minimum: `transform-custom:*` on `Resource: "*"`.

| Permission | Operation |
|-----------|----------|
| `transform-custom:ConverseStream` | Interactive conversations |
| `transform-custom:ExecuteTransformation` | Execute transforms |
| `transform-custom:ListTransformationPackageMetadata` | List transforms (`atx custom def list --json`) |
| `transform-custom:DeleteTransformationPackage` | Delete transforms |
| `transform-custom:CompleteTransformationPackageUpload` | Upload TDs |
| `transform-custom:CreateTransformationPackageUrl` | Create upload URLs |
| `transform-custom:GetTransformationPackageUrl` | Download TDs |
| `transform-custom:ListKnowledgeItems` | List knowledge items |
| `transform-custom:GetKnowledgeItem` | View knowledge item details |
| `transform-custom:DeleteKnowledgeItem` | Delete knowledge items |
| `transform-custom:UpdateKnowledgeItemConfiguration` | Configure auto-approval |
| `transform-custom:UpdateKnowledgeItemStatus` | Enable/disable items |
| `transform-custom:ListTagsForResource` | List tags |
| `transform-custom:TagResource` | Add tags |
| `transform-custom:UntagResource` | Remove tags |
