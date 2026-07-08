---
name: "graviton-migration-power"
displayName: "Plan and Migration to Graviton Power"
description: "Analyzes source code to identify compatibilities with Graviton processors(Arm64 architecture). Generates reports with incompatibilities and provides suggestions for minimal required and recommended versions for language runtimes and dependency libraries."
keywords: ["ec2", "graviton", "arm", "migration", "porting", "dependencies", "compatibilities", "arm64", "aarch64"]
author: "AWS"
---

# Graviton Migration Power

## Overview

Migrates codebases from x86 to AWS Graviton (Arm64). Scans Dockerfiles, dependency manifests, and source code to identify architecture-specific issues, then provides actionable fixes.

---

## Migration Workflow

Copy this checklist and track progress:

```
Migration Progress:
- [ ] Step 1: Verify prerequisites (Docker running)
- [ ] Step 2: Check Dockerfiles for ARM64 base image compatibility
- [ ] Step 3: Verify packages installed in Dockerfiles
- [ ] Step 4: Check dependency manifests (requirements.txt, pom.xml, go.mod, package.json)
- [ ] Step 5: Determine language and run migrate_ease_scan
- [ ] Step 6: Generate migration report
- [ ] Step 7: Get user confirmation before making changes
- [ ] Step 8: Apply changes
```

### Step 1: Verify Prerequisites

**CRITICAL**: Docker must be running. If not, stop and inform the user.

```bash
docker ps
```

If this fails, do NOT proceed. Tell the user to start Docker Desktop.

### Step 2: Check Dockerfiles for Base Image Compatibility

For each Dockerfile found in the project:

1. Extract the base image (e.g., `FROM eclipse-temurin:17-jdk-alpine`)
2. Run `check_image` or `skopeo` to verify ARM64 support
3. If image lacks ARM64 support → find a multi-arch alternative

**Validation**: Confirm the replacement image supports BOTH `amd64` AND `arm64` before recommending it.

### Step 3: Verify Packages Installed in Dockerfiles

For each package installed via `apt-get`, `apk`, `yum`, or `pip` inside Dockerfiles:

1. Send to `knowledge_base_search`: "Is [package] compatible with Arm architecture?"
2. If incompatible → suggest compatible version or alternative

### Step 4: Check Dependency Manifests

**Python projects** (requirements.txt, setup.py, pyproject.toml):
→ Check each package with `knowledge_base_search`
→ Focus on packages with native C extensions

**Java projects** (pom.xml, build.gradle):
→ Check native dependencies (Netty classifiers, JNI libraries)
→ Look for architecture-specific classifiers like `linux-x86_64`

**Go projects** (go.mod):
→ Check CGO dependencies
→ Look for platform-specific build tags

**JavaScript/Node.js** (package.json):
→ Check native addons (node-gyp based packages)
→ Look for platform-specific optional dependencies

**C/C++** (Makefile, CMakeLists.txt):
→ Check for x86 intrinsics, inline assembly
→ Look for architecture-specific compiler flags

### Step 5: Run migrate_ease_scan

Determine the primary language, then run the appropriate scanner:

| Language | Scanner |
|----------|---------|
| Python | `python` |
| Java | `java` |
| Go | `go` |
| JavaScript | `js` |
| C/C++ | `cpp` |

**Validation**: Review scan results for false positives before including in report.

### Step 6: Generate Migration Report

Use the report template below. Do NOT proceed to changes without user review.

### Step 7: Get User Confirmation

Present the report and explicitly ask: "Would you like me to apply these changes?"

**Do NOT modify any files until the user confirms.**

### Step 8: Apply Changes

Apply changes one file at a time. After each file, briefly state what was changed.

---

## Report Template

Use this structure for all migration reports:

```markdown
# Graviton Migration Report

## Summary
[One paragraph: project type, total issues found, severity breakdown (critical/warning/info)]

## Docker Images

| Image | Source File | ARM64 Support | Action Required |
|-------|------------|---------------|-----------------|
| `image:tag` | Dockerfile | ❌ / ✅ | Replace with `image:tag` / None |

## Dependencies

| Package | Version | File | ARM64 Compatible | Action |
|---------|---------|------|------------------|--------|
| `pkg` | x.y.z | requirements.txt | ❌ / ✅ | Upgrade to x.y.z / None |

## Source Code Scan Results

**Scanner used**: [language] scanner
**Files scanned**: [count]
**Issues found**: [count]

[List each issue with file path, line number if available, and recommended fix]

## Recommendations (Priority Order)

1. [Critical] ...
2. [Critical] ...
3. [Warning] ...
4. [Info] ...

## Build Instructions

### Multi-Architecture Docker Build
```bash
docker buildx create --name multiarch --use --bootstrap
docker buildx build -t your-registry/app:latest \
  --platform linux/amd64,linux/arm64 \
  --push .
```
```

---

## Examples

### Example: Checking a Docker Image

**Input**: Dockerfile contains `FROM eclipse-temurin:17-jdk-alpine`

**Steps**:
1. Run `check_image` on `eclipse-temurin:17-jdk-alpine`
2. Result: x86_64 only ❌
3. Run `check_image` on `eclipse-temurin:17-jdk`
4. Result: supports amd64, arm64 ✅

**Report entry**:
| `eclipse-temurin:17-jdk-alpine` | Dockerfile | ❌ | Replace with `eclipse-temurin:17-jdk` |

### Example: Checking a Python Dependency

**Input**: requirements.txt contains `grpcio==1.48.0`

**Steps**:
1. Query `knowledge_base_search`: "Is grpcio compatible with Arm architecture?"
2. Result: grpcio 1.48.0+ provides ARM64 wheels ✅

**Report entry**:
| `grpcio` | 1.48.0 | requirements.txt | ✅ | None |

### Example: Netty Native Transport (Java)

**Input**: pom.xml contains:
```xml
<dependency>
    <groupId>io.netty</groupId>
    <artifactId>netty-transport-native-epoll</artifactId>
    <classifier>linux-x86_64</classifier>
</dependency>
```

**Steps**:
1. Identify x86_64-specific classifier
2. Query `knowledge_base_search`: "Is netty-transport-native-epoll compatible with Arm architecture?"
3. Result: Needs additional `linux-aarch_64` classifier

**Fix**: Add alongside existing:
```xml
<dependency>
    <groupId>io.netty</groupId>
    <artifactId>netty-transport-native-epoll</artifactId>
    <classifier>linux-aarch_64</classifier>
</dependency>
```

---

## Degrees of Freedom

**Low freedom (follow exactly)**:
- The checklist order (Steps 1-8)
- Never modify files without user confirmation (Step 7)
- Always verify Docker is running before proceeding
- Use the report template structure

**High freedom (adapt to context)**:
- How to phrase knowledge_base_search queries
- Which alternative images to suggest (pick best multi-arch option)
- How to organize findings within report sections
- Level of detail in recommendations based on project complexity

---

## Troubleshooting

### Docker Not Running

**Symptom**: MCP server fails to start, tools return connection errors
**Fix**: Tell user to start Docker Desktop and retry

### Scan Timeout

**Symptom**: `migrate_ease_scan` hangs or returns timeout error
**Cause**: Large codebase or slow Docker volume mount
**Fix**: Try scanning a subdirectory, or suggest user increase Docker resource limits

### Image Not Found

**Symptom**: `check_image` or `skopeo` returns "not found"
**Cause**: Private registry requiring authentication, or typo in image name
**Fix**: Verify image name is correct. For private images, inform user that manual verification is needed.

### Knowledge Base Returns No Results

**Symptom**: `knowledge_base_search` returns empty or irrelevant results
**Fix**: Rephrase query. Try: "Is [package] [version] compatible with ARM64 aarch64?"
If still no results, note the package as "unknown compatibility - manual verification recommended"

### Scan Reports False Positives

**Symptom**: `migrate_ease_scan` flags code that is actually architecture-neutral
**Fix**: Review each finding. If the flagged code doesn't use architecture-specific features (intrinsics, inline assembly, platform-specific paths), mark as false positive in the report.

---

## Onboarding

### Prerequisites

1. **Docker Desktop**: Required for the Arm MCP server
   - Verify: `docker --version`
   - Confirm running: `docker ps`

2. **Git** (optional): For scanning remote repositories
   - Verify: `git --version`

### Available Tools

| Tool | Purpose |
|------|---------|
| `migrate_ease_scan` | Scan codebase for Arm compatibility issues |
| `skopeo` | Inspect container images for architecture support |
| `knowledge_base_search` | Search Arm documentation for package compatibility |
| `check_image` | Quick Docker image architecture check |
| `mca` | Machine Code Analyzer for assembly performance |

---

## Steering Files

- **karpenter.md** — Karpenter NodePool/EC2NodeClass migration to Graviton instances
- **build-pipelines.md** — CI/CD pipeline adjustments for multi-arch builds

---

## License & Legal

### Power License

Provided by AWS, subject to the AWS Customer Agreement and applicable service terms.

### MCP Server

- **arm-mcp** (`armlimited/arm-mcp:latest`): Docker container with Arm migration tools
  - License: https://github.com/arm/mcp/blob/main/LICENSE

### Third-Party

- Docker: https://www.docker.com/legal/docker-subscription-service-agreement/

---

## Additional Resources

- AWS Graviton Technical Guide: https://github.com/aws/aws-graviton-getting-started
- Arm Architecture Reference: Available via `knowledge_base_search`

---

**Supported Languages**: C++, Python, Go, JavaScript, Java
**Container Runtime**: Docker required
**MCP Server**: arm-mcp (Docker-based)
