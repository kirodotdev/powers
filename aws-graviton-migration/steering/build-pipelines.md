# Build Pipeline Migration to Graviton (ARM64)

## Contents
- [Workflow Checklist](#workflow-checklist)
- [Decision Tree: Which Sections Apply](#decision-tree-which-sections-apply)
- [Detection](#detection)
- [Migration Steps](#migration-steps)
  - [1. Multi-Architecture Container Builds](#1-multi-architecture-container-builds)
  - [2. Dockerfile Adjustments](#2-dockerfile-adjustments)
  - [3. Build Runner Configuration](#3-build-runner-configuration)
  - [4. Dual-Architecture Testing](#4-dual-architecture-testing)
  - [5. Native Compilation Flags](#5-native-compilation-flags)
  - [6. Post-Migration Cleanup](#6-post-migration-cleanup)
- [Example: Full Before → After](#example-full-before--after)
- [Common Pitfalls](#common-pitfalls)
- [Troubleshooting](#troubleshooting)
- [References](#references)

---

## Workflow Checklist

Copy and track progress:

```
Build Pipeline Migration Progress:
- [ ] Step 1: Detect CI/CD configs and architecture-specific settings
- [ ] Step 2: Verify base images are multi-arch
- [ ] Step 3: Update Docker builds to produce multi-arch images
- [ ] Step 4: Update Dockerfile for architecture-agnostic deps
- [ ] Step 5: Configure ARM64 build runner (if needed)
- [ ] Step 6: Test build output on ARM64
- [ ] Step 7: Update build matrix for dual-arch testing (optional)
- [ ] Step 8: Post-migration cleanup
```

**Steps 1-4 are mandatory.** Steps 5-7 depend on your CI system and project type. Step 8 happens after full migration.

---

## Decision Tree: Which Sections Apply

Not every section applies to every project. Use this to focus:

**What CI system?**
- GitHub Actions → [Multi-Arch Builds (GitHub)](#github-actions) + [Runner Config (GitHub)](#github-actions-self-hosted-arm64-runner)
- AWS CodeBuild → [Multi-Arch Builds (CodeBuild)](#aws-codebuild)
- GitLab CI → [Runner Config (GitLab)](#gitlab-ci-arm64-runner-tag)
- Jenkins → [Runner Config (Jenkins)](#jenkins-arm64-agent-label)
- Other / shell scripts → [Multi-Arch Builds (CLI)](#docker-buildx-with-remote-native-builders)

**Does the project compile native code (C/C++, Rust, Go with CGO)?**
- Yes → Read [Native Compilation Flags](#5-native-compilation-flags)
- No → Skip that section

**Does the Dockerfile download architecture-specific binaries?**
- Yes → Read [Dockerfile Adjustments](#2-dockerfile-adjustments)
- No → Skip that section

---

## Detection

Scan the workspace for:

- CI/CD config files: `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml`, `.circleci/config.yml`, `bitbucket-pipelines.yml`
- Build scripts referencing `x86_64`, `amd64`, `linux/amd64`
- Docker build commands without `--platform` or with hardcoded `linux/amd64`
- Container image tags with architecture suffixes (`:latest-amd64`)
- Build matrices that only include x86 targets
- Terraform/CloudFormation provisioning build infra on x86 instance types
- Makefiles or shell scripts with architecture-conditional logic

---

## Migration Steps

### 1. Multi-Architecture Container Builds

Produce images that work on both x86 and Graviton. Always use native ARM64 build runners rather than QEMU emulation (5-10x slower, unreliable builds).

#### GitHub Actions

Separate native runners per architecture, merged into one manifest:

```yaml
jobs:
  build-amd64:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE }}:${{ env.TAG }}-amd64

  build-arm64:
    runs-on: [self-hosted, linux, arm64]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/arm64
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE }}:${{ env.TAG }}-arm64

  manifest:
    needs: [build-amd64, build-arm64]
    runs-on: ubuntu-latest
    steps:
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
      - run: |
          docker manifest create ${{ env.REGISTRY }}/${{ env.IMAGE }}:${{ env.TAG }} \
            ${{ env.REGISTRY }}/${{ env.IMAGE }}:${{ env.TAG }}-amd64 \
            ${{ env.REGISTRY }}/${{ env.IMAGE }}:${{ env.TAG }}-arm64
          docker manifest push ${{ env.REGISTRY }}/${{ env.IMAGE }}:${{ env.TAG }}
```

#### Docker Buildx with Remote Native Builders

For CLI, Jenkinsfile, or shell scripts:

```bash
docker buildx create --name multiarch-builder --platform linux/amd64 --node builder-amd64 unix:///var/run/docker.sock
docker buildx create --name multiarch-builder --append --platform linux/arm64 --node builder-arm64 ssh://user@arm64-host
docker buildx use multiarch-builder

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ${REGISTRY}/${IMAGE}:${TAG} \
  --push .
```

#### AWS CodeBuild

Use a Graviton-based environment for native ARM64 builds:

```json
{
  "environment": {
    "type": "ARM_CONTAINER",
    "image": "aws/codebuild/amazonlinux2-aarch64-standard:3.0",
    "computeType": "BUILD_GENERAL1_LARGE"
  }
}
```

For multi-arch: use separate CodeBuild projects (x86 + Graviton), then create a manifest in a third step.

**Validation gate**: After building, verify the manifest contains both architectures:

```bash
docker manifest inspect ${REGISTRY}/${IMAGE}:${TAG} | grep architecture
# Should show both "amd64" and "arm64"
```

### 2. Dockerfile Adjustments

#### Use Multi-Arch Base Images

```dockerfile
# Good: official images are multi-arch
FROM python:3.12-slim
FROM node:20-alpine
FROM amazoncorretto:21

# Bad: architecture-specific tags
# FROM amd64/python:3.12-slim
```

**Validation gate**: Use `check_image` or `skopeo` to verify the base image supports `linux/arm64`.

#### Handle Architecture-Specific Binaries

Use Docker's built-in `TARGETARCH` variable:

```dockerfile
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm64" ]; then \
      curl -L https://example.com/tool-arm64.tar.gz -o tool.tar.gz; \
    else \
      curl -L https://example.com/tool-amd64.tar.gz -o tool.tar.gz; \
    fi && \
    tar -xzf tool.tar.gz -C /usr/local/bin/
```

`TARGETARCH` is automatically set by Docker Buildx during multi-platform builds.

### 3. Build Runner Configuration

Only needed if your CI uses self-hosted runners and you need native ARM64 builds.

#### GitHub Actions (Self-Hosted ARM64 Runner)

```yaml
jobs:
  build-arm64:
    runs-on: [self-hosted, linux, arm64]
    steps:
      - uses: actions/checkout@v4
      - run: make build
```

#### GitLab CI (ARM64 Runner Tag)

```yaml
build:
  tags:
    - arm64
  script:
    - make build
```

#### Jenkins (ARM64 Agent Label)

```groovy
pipeline {
  agent { label 'arm64' }
  stages {
    stage('Build') {
      steps {
        sh 'make build'
      }
    }
  }
}
```

### 4. Dual-Architecture Testing

Run tests on both architectures during migration to catch issues early.

```yaml
# GitHub Actions matrix example
jobs:
  test:
    strategy:
      matrix:
        arch: [amd64, arm64]
        include:
          - arch: amd64
            runner: ubuntu-latest
          - arch: arm64
            runner: [self-hosted, linux, arm64]
    runs-on: ${{ matrix.runner }}
    steps:
      - uses: actions/checkout@v4
      - run: make test
```

**Validation gate**: Both architecture builds must pass before merging.

### 5. Native Compilation Flags

**Only applies if the project compiles native code (C/C++, Rust, Go with CGO).**

Check for:
- Hardcoded `-march=x86-64` or `-mtune` flags
- x86 SIMD intrinsics (`SSE`, `AVX`) → need ARM equivalents (`NEON`, `SVE`)
- Assembly files (`.s`, `.asm`) with x86 instructions
- `GOARCH=amd64` hardcoded in build scripts

#### Go

```bash
# On ARM64 runner, GOARCH defaults to arm64
go build -o app

# For cross-build (prefer native builds instead):
GOOS=linux GOARCH=arm64 go build -o app-arm64
```

#### Rust

```bash
# On ARM64 runner, default target is aarch64
cargo build --release
```

### 6. Post-Migration Cleanup

After all workloads run on Graviton:

- Remove `linux/amd64` from build targets if x86 no longer needed
- Remove architecture-conditional logic from Dockerfiles
- Switch build infrastructure to Graviton instances for cost savings
- Consolidate per-architecture jobs into single ARM64-native jobs

---

## Example: Full Before → After

### Before: GitHub Actions (x86-only)

```yaml
name: Build and Push
on: push

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t myregistry/myapp:latest .
      - run: docker push myregistry/myapp:latest
```

### After: GitHub Actions (multi-arch with native runners)

```yaml
name: Build and Push (Multi-Arch)
on: push

jobs:
  build-amd64:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: myregistry
      - uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64
          push: true
          tags: myregistry/myapp:latest-amd64

  build-arm64:
    runs-on: [self-hosted, linux, arm64]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: myregistry
      - uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/arm64
          push: true
          tags: myregistry/myapp:latest-arm64

  manifest:
    needs: [build-amd64, build-arm64]
    runs-on: ubuntu-latest
    steps:
      - uses: docker/login-action@v3
        with:
          registry: myregistry
      - run: |
          docker manifest create myregistry/myapp:latest \
            myregistry/myapp:latest-amd64 \
            myregistry/myapp:latest-arm64
          docker manifest push myregistry/myapp:latest
```

---

## Common Pitfalls

| Issue | Symptom | Fix |
|-------|---------|-----|
| Missing multi-arch manifest | `exec format error` at runtime | Build per-arch on native runners, create manifest |
| x86-only binary downloads in Dockerfile | Build fails on ARM64 | Use `TARGETARCH` to select correct binary |
| Hardcoded `amd64` in image tags | Wrong image pulled on Graviton nodes | Use multi-arch tags or manifest lists |
| Native extensions not compiled for ARM64 | Import errors or segfaults | Rebuild native deps on ARM64 build runner |
| Shared build cache across architectures | Corrupt or wrong-arch artifacts | Separate build caches by architecture |
| QEMU emulation used instead of native runners | Builds 5-10x slower, intermittent failures | Use native ARM64 runners or remote builders |

---

## Troubleshooting

### Build Fails with "exec format error"

**Symptom**: Docker build step fails immediately with `exec format error`
**Cause**: Trying to run x86 binary on ARM64 runner (or vice versa) without emulation
**Fix**: Ensure you're building with `--platform` matching the runner architecture, or use native runners per arch.

### ARM64 Runner Not Available

**Symptom**: Job stays queued with "waiting for runner"
**Cause**: No self-hosted ARM64 runner registered, or runner is offline
**Fix**:
1. For GitHub Actions: Set up a self-hosted runner on a Graviton instance
2. For CodeBuild: Use `ARM_CONTAINER` environment type
3. For GitLab: Register a runner with the `arm64` tag on a Graviton instance

### Multi-Arch Manifest Push Fails

**Symptom**: `docker manifest push` returns authentication or "not found" error
**Cause**: Per-arch images not pushed yet, or registry login expired between jobs
**Fix**: Ensure per-arch images are pushed before the manifest job runs. Re-authenticate in the manifest job.

### Native Dependency Compilation Fails on ARM64

**Symptom**: `pip install` or `npm install` fails with compilation errors on ARM64 runner
**Cause**: Package has C extensions that need ARM64-specific build tools
**Fix**:
1. Install build essentials: `apt-get install build-essential`
2. Check if a pre-built ARM64 wheel/binary exists (newer version may have it)
3. If no ARM64 support exists, flag as migration blocker

---

## References

- [AWS Graviton Getting Started — CI/CD](https://github.com/aws/aws-graviton-getting-started/blob/main/containers.md)
- [Docker Multi-Platform Builds](https://docs.docker.com/build/building/multi-platform/)
- [AWS CodeBuild ARM Support](https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref-compute-types.html)
- [GitHub Actions Runner Images](https://github.com/actions/runner-images)
