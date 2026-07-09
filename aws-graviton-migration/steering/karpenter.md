# Karpenter Configuration Migration to Graviton (ARM64)

## Contents
- [Workflow Checklist](#workflow-checklist)
- [Detection](#detection)
- [Migration Strategy](#migration-strategy)
- [Instance Family Mappings](#instance-family-mappings)
- [Example: Full Before → After](#example-full-before--after)
- [Key Checks](#key-checks)
- [Troubleshooting](#troubleshooting)
- [References](#references)

---

## Workflow Checklist

Copy and track progress:

```
Karpenter Migration Progress:
- [ ] Step 1: Detect Karpenter configs in workspace
- [ ] Step 2: Verify container images support ARM64
- [ ] Step 3: Create dedicated Graviton NodePool (with taint)
- [ ] Step 4: Add tolerations to target workloads
- [ ] Step 5: Validate pods schedule on Graviton nodes
- [ ] Step 6: Pin validated workloads to ARM64 (nodeSelector)
- [ ] Step 7: Post-migration cleanup (remove taints, delete old NodePool)
```

**Steps 1-4 are mandatory in order.** Steps 5-7 are iterative — repeat per workload until all are migrated.

---

## Detection

Scan the workspace for these indicators:

- YAML files containing `apiVersion: karpenter.sh/v1` or `karpenter.sh/v1beta1`
- Resources of `kind: NodePool` and `kind: EC2NodeClass`
- `kubernetes.io/arch` requirements set to `amd64` only
- Instance family requirements using x86-only families (`m5`, `c5`, `r5`, `t3`)
- Workload manifests with `nodeSelector` or `tolerations` referencing architecture
- Helm values files with instance-type or architecture settings

---

## Migration Strategy

### Step 1: Detect Existing Configuration

Identify all NodePool resources. Note current instance families and architecture constraints.

### Step 2: Verify Image Compatibility

**Before creating the Graviton NodePool**, verify ALL container images support `linux/arm64`:
- Application images
- Sidecar containers (service mesh proxies, logging agents)
- DaemonSets
- Init containers

Use `check_image` or `skopeo` tools to verify each image.

**Validation gate**: Do NOT proceed to Step 3 until all images are confirmed ARM64-compatible. If any image lacks support, flag it in the migration report and resolve first.

### Step 3: Create a Dedicated Graviton NodePool

Create a **separate** NodePool with a taint. This allows gradual rollout without disrupting existing workloads.

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: graviton
spec:
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
  template:
    spec:
      terminationGracePeriod: 24h
      expireAfter: 720h
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      taints:
        - key: graviton-migration
          effect: NoSchedule
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand", "spot"]
        - key: kubernetes.io/arch
          operator: In
          values: ["arm64"]
        - key: karpenter.k8s.aws/instance-generation
          operator: Gt
          values: ["4"]
```

**Validation gate**: Run `kubectl get nodepool graviton` to confirm it's created. Check Karpenter controller logs for errors.

### Step 4: Add Tolerations to Workloads

For each workload being migrated, add the toleration:

```yaml
spec:
  tolerations:
    - key: graviton-migration
      operator: Exists
```

### Step 5: Validate Scheduling

**Validation gate**: Confirm pods are running on Graviton nodes before proceeding.

```bash
# Check pod is on an ARM64 node
kubectl get pod <pod-name> -o jsonpath='{.spec.nodeName}' | xargs kubectl get node -o jsonpath='{.metadata.labels.kubernetes\.io/arch}'
# Expected: arm64
```

If pods stay Pending or CrashLoop, see [Troubleshooting](#troubleshooting).

### Step 6: Pin Validated Workloads to Graviton

Once a workload is validated on ARM64, add `nodeSelector` to lock it in:

```yaml
spec:
  nodeSelector:
    kubernetes.io/arch: arm64
  tolerations:
    - key: graviton-migration
      operator: Exists
```

### Step 7: Post-Migration Cleanup

After ALL workloads are migrated and stable:

1. Remove the `graviton-migration` taint from the Graviton NodePool
2. Remove tolerations and nodeSelectors from workload specs
3. Delete the old x86-only NodePool

---

## Instance Family Mappings

| x86 Family | Graviton Equivalent | Notes |
|------------|-------------------|-------|
| m5, m6i | m6g, m7g | General purpose |
| c5, c6i | c6g, c7g | Compute optimized |
| r5, r6i | r6g, r7g | Memory optimized |
| t3 | t4g | Burstable |

---

## Example: Full Before → After

### Before (x86-only NodePool)

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["m5.large", "m5.xlarge", "c5.large"]
```

### After (Graviton NodePool added alongside)

```yaml
# Existing x86 NodePool (keep during migration)
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["m5.large", "m5.xlarge", "c5.large"]
---
# New Graviton NodePool
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: graviton
spec:
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
  template:
    spec:
      expireAfter: 720h
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      taints:
        - key: graviton-migration
          effect: NoSchedule
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand", "spot"]
        - key: kubernetes.io/arch
          operator: In
          values: ["arm64"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["m7g.large", "m7g.xlarge", "c7g.large"]
```

### Workload Deployment (migrated)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/arch: arm64
      tolerations:
        - key: graviton-migration
          operator: Exists
      containers:
        - name: app
          image: my-registry/my-app:latest  # Must support linux/arm64
```

---

## Key Checks

- Verify ALL container images support `linux/arm64` before creating the NodePool
- Check sidecar containers (service mesh proxies, logging agents)
- Check DaemonSets for ARM64 compatibility
- Validate init containers have ARM64 images
- Use `check_image` or `skopeo` tools to verify image architecture support
- Run `migrate_ease_scan` on application source code if architecture-specific code is suspected

---

## Troubleshooting

### Pods Stay Pending After Adding Toleration

**Symptom**: Pod remains in `Pending` state, no node provisioned.

**Causes & Fixes**:
1. **NodePool not creating nodes** — Check Karpenter controller logs: `kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter`
2. **Instance type unavailable** — Widen the instance family list or add more AZs
3. **Missing toleration** — Verify the pod spec has the exact taint key match

### CrashLoopBackOff on Graviton Nodes

**Symptom**: Pod starts on ARM64 node but crashes immediately.

**Causes & Fixes**:
1. **Image is x86-only** — `exec format error` in logs. Rebuild image for ARM64 or use multi-arch image.
2. **Native dependency missing ARM64 build** — Check container logs for missing `.so` files. Rebuild the dependency on ARM64.
3. **Architecture-specific code path** — Run `migrate_ease_scan` on the source code.

### Wrong Nodes Selected

**Symptom**: Pods land on x86 nodes instead of Graviton.

**Causes & Fixes**:
1. **Toleration added but no nodeSelector** — Without `nodeSelector`, the scheduler may still pick x86 nodes. Add `nodeSelector: kubernetes.io/arch: arm64` to force ARM64.
2. **Karpenter consolidation moved pods** — Check if consolidation policy is moving pods back. Ensure the x86 NodePool doesn't accept the workload.

---

## References

- [Migrating from x86 to Graviton on EKS using Karpenter](https://aws.amazon.com/blogs/containers/migrating-from-x86-to-aws-graviton-on-amazon-eks-using-karpenter/)
- [Karpenter NodePool docs](https://karpenter.sh/docs/concepts/nodepools/)
- [AWS Graviton Getting Started](https://github.com/aws/aws-graviton-getting-started)
