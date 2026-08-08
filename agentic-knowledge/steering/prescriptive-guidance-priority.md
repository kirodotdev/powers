---
inclusion: always
---

# AWS Prescriptive Guidance Priority

## Primary Knowledge Sources

**ALWAYS start by searching these specific AWS prescriptive guidance documents** using the AWS Knowledge MCP server (https://knowledge-mcp.global.api.aws):

### 1. Foundations of Agentic AI on AWS
- **Search Terms**: "foundations of agentic AI", "agentic AI fundamentals", "autonomous systems AWS"
- **Priority**: HIGHEST - This is the foundational document for all agentic AI concepts
- **Use For**: Core definitions, principles, and architectural foundations

### 2. Agentic AI Patterns and Workflows on AWS
- **Search Terms**: "agentic AI patterns", "agentic workflows", "agent patterns AWS"
- **Priority**: HIGHEST - This contains the specific patterns and implementation approaches
- **Use For**: Architectural patterns, workflow designs, and implementation strategies

### 3. Agentic AI Frameworks, Protocols, and Tools on AWS
- **Search Terms**: "agentic AI frameworks", "agent protocols", "agentic tools AWS"
- **Priority**: HIGH - This covers the modern frameworks and integration approaches
- **Use For**: Framework selection, protocol implementation, and tool integration

### 4. Building Serverless Architectures for Agentic AI on AWS
- **Search Terms**: "serverless agentic AI", "agentic serverless architecture"
- **Priority**: HIGH - This covers deployment and scaling patterns
- **Use For**: Deployment strategies, scaling approaches, and serverless patterns

### 5. Building Multi-Tenant Architectures for Agentic AI on AWS
- **Search Terms**: "multi-tenant agentic AI", "agentic multi-tenancy"
- **Priority**: MEDIUM - This covers enterprise and SaaS deployment patterns
- **Use For**: Enterprise architectures, multi-tenancy, and isolation strategies

## Search Strategy Priority

### Step 1: Always Search Prescriptive Guidance First
Before providing any architectural recommendations, ALWAYS search the AWS Knowledge MCP server for relevant content from these prescriptive guidance documents.

**Example Search Queries:**
- "foundations of agentic AI autonomous agents"
- "agentic AI patterns multi-agent collaboration"
- "agentic workflows serverless architecture"
- "agentic AI frameworks Strands AgentCore"

### Step 2: Supplement with Framework Documentation
After establishing the foundational guidance, supplement with:
- Strands Agent SDK documentation for implementation details
- AgentCore platform documentation for deployment specifics
- Current AWS service documentation for technical details

### Step 3: Synthesize Comprehensive Recommendations
Combine the prescriptive guidance with framework-specific documentation to provide:
- Architecturally sound recommendations based on AWS best practices
- Modern implementation approaches using current frameworks
- Specific deployment and scaling strategies

## Response Pattern

### Always Lead With Prescriptive Guidance
Start every architectural recommendation with:
1. **"Based on AWS prescriptive guidance on [specific document]..."**
2. **Quote or reference specific sections** from the foundational documents
3. **Then supplement** with framework-specific implementation details

### Example Response Structure:
```
Based on AWS prescriptive guidance on "Foundations of Agentic AI on AWS", 
agentic systems are characterized by [specific guidance from document].

The "Agentic AI Patterns and Workflows" guidance recommends [specific pattern] 
for your use case because [reasoning from document].

To implement this using modern frameworks:
- Strands Agent SDK provides [specific capability]
- AgentCore platform offers [specific service]
- [Implementation details from framework documentation]
```

## Quality Assurance

### Verify Prescriptive Guidance Coverage
Before finalizing any recommendation, ensure you have:
- ✅ Searched the foundational prescriptive guidance documents
- ✅ Referenced specific patterns or principles from those documents
- ✅ Aligned framework recommendations with prescriptive guidance
- ✅ Provided implementation details that follow AWS best practices

### Avoid Generic Recommendations
- ❌ Don't provide generic "best practices" without prescriptive guidance backing
- ❌ Don't recommend patterns that aren't supported by AWS guidance
- ❌ Don't skip the foundational document search step
- ❌ Don't ignore user-specific constraints or requirements
- ✅ Always ground recommendations in official AWS prescriptive guidance
- ✅ Tailor recommendations to user's specific context and constraints
- ✅ Provide implementation roadmaps with concrete next steps
- ✅ Address security, scalability, and operational considerations