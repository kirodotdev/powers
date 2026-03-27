---
inclusion: manual
---

# Karpenter Configuration Migration to Graviton (ARM64)

This steering file guides the detection and migration of Karpenter configurations to use AWS Graviton (ARM64) instances.

## Detection

When analyzing a workspace for Karpenter configurations, look for:

- YAML files containing `apiVersion: karpenter.sh/v1` or `karpenter.sh/v1beta1`
- Resources of `kind: NodePool` and `kind: EC2NodeClass`
- Existing `kubernetes.io/arch` requirements set to `amd64` only
- Instance family requirements using x86-only families (e.g., `m5`, `c5`, `r5`)
- Any `nodeSelector` or `tolerations` in workload manifests referencing architecture
- Helm values files with architecture or instance-type settings for Karpenter

## Migration Strategy

Follow a gradual rollout approach:

### 1. Create a Dedicated Graviton NodePool

Create a separate NodePool for Graviton nodes rather than modifying the existing x86 NodePool. This gives independent control over instance selection and rollout pace.

Example Graviton NodePool:

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

### 2. Add Tolerations to Workloads

For each workload being migrated, add a toleration for the Graviton taint:

```yaml
spec:
  tolerations:
    - key: graviton-migration
      operator: Exists
```

### 3. Force Scheduling on Graviton (After Validation)

Once a workload is validated on ARM64, pin it to Graviton nodes:

```yaml
spec:
  nodeSelector:
    kubernetes.io/arch: arm64
  tolerations:
    - key: graviton-migration
      operator: Exists
```

### 4. Post-Migration Cleanup

After all workloads are migrated:

- Remove the `graviton-migration` taint from the Graviton NodePool
- Remove tolerations and nodeSelectors from workload specs
- Delete the old x86-only NodePool

## Common x86 to Graviton Instance Family Mappings

| x86 Family | Graviton Equivalent | Notes |
|------------|-------------------|-------|
| m5, m6i    | m6g, m7g          | General purpose |
| c5, c6i    | c6g, c7g          | Compute optimized |
| r5, r6i    | r6g, r7g          | Memory optimized |
| t3          | t4g               | Burstable |

## Key Checks

- Verify all container images support `linux/arm64` (multi-arch or ARM64-specific)
- Check sidecar containers (service mesh proxies, logging agents) for ARM64 support
- Check DaemonSets for ARM64 compatibility
- Validate any init containers also have ARM64 images
- Use the `check_image` or `skopeo` tools from the Graviton Migration Power to verify image architecture support
- Run `migrate_ease_scan` on application source code to detect architecture-specific code

## References

- [Migrating from x86 to Graviton on EKS using Karpenter](https://aws.amazon.com/blogs/containers/migrating-from-x86-to-aws-graviton-on-amazon-eks-using-karpenter/)
- [Karpenter NodePool docs](https://karpenter.sh/docs/concepts/nodepools/)
- [AWS Graviton Getting Started](https://github.com/aws/aws-graviton-getting-started)
