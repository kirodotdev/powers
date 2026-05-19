# Workflow: Writing an SDP Customer Reference from Project Documents

Follow this process when the user has project documents and needs to write a customer reference case.

## Step 1 — Gather and Read Documents

Request or read the following documents in priority order:

| Document | What to Extract |
|---|---|
| Closure report / delivery acceptance | Real dates, delivered scope, customer signatories |
| Technical spec / Architecture doc | AWS services, architecture, Account IDs, subnets, configurations |
| Economic proposal / SOW | Start date, original scope, proposed services |
| Architecture diagrams | Attach directly to the SDP form |
| Emails or meeting minutes | Additional context, outcomes mentioned by the customer |

## Step 2 — Extract Key Information

With the available documents, identify and note:

**About the customer:**
- Full name and type of organization (sector, country)
- Involved AWS Account ID(s)
- Contact who can validate the case with AWS (name + title)

**About the project:**
- Full list of AWS services used
- Original problem that motivated the engagement
- Dates: start, end, go-live (if sub-projects exist, dates for each)
- Third-party tools involved

**About the outcomes:**
- Any documented metrics (latency, cost, availability, time)
- Clear qualitative benefits even without exact numbers
- Resolved problems that are verifiable by the customer

## Step 3 — Draft "Customer Challenge" Field

**Length**: 3–5 paragraphs (300–500 words)

**Structure**:
1. Customer context (who they are, industry, scale of operations)
2. Specific technical problem (what wasn't working or was missing)
3. Why it was critical or urgent to solve
4. Limitations of the previous approach (if applicable)

**Rules**:
- Write from the customer's perspective
- Do NOT mention the partner/implementer in this section
- Use language the customer would recognize as their own
- Avoid generic phrases like "they needed to improve their cloud infrastructure"

**Example of a strong opening**:
> "[Customer] operates [N] business-critical applications distributed across [N] AWS accounts under an AWS Control Tower organization. Without a centralized network layer, each new project required manually configuring bilateral connectivity, increasing operational risk and deployment lead times."

## Step 4 — Draft "Proposed Solution" Field

**Length**: 4–7 technical paragraphs + services table

**Structure**:
1. Introductory paragraph: high-level architecture overview
2. One paragraph per major component (use exact AWS service names)
3. Mandatory table: AWS Service | Role in the solution
4. Mention of the Well-Architected Framework if applicable

**Expected level of detail**:
- Exact names: "Amazon Aurora PostgreSQL" not "database"
- Relevant configurations: number of AZs, CIDRs, number of instances
- Data flow between components

**Service table template**:
```
| AWS Service | Role in the Solution |
|---|---|
| [Service] | [What it specifically does in this project] |
```

## Step 5 — Complete Date Fields

If there are multiple sub-projects, document dates per sub-project:

```
Start date: [date of first kickoff or accepted proposal]
End date: [date of last closure report]
Production date: [real go-live date, most recent if phased]
```

If there is only one closure report, use that date as the reference for end and production.

## Step 6 — Draft "Results/Outcomes" Field

**Impact order for AWS**:
1. Business metrics (cost savings, speed, revenue)
2. Measurable technical metrics (latency ms, uptime %, throughput RPS)
3. Operational improvements (reduced tickets, eliminated manual processes)
4. Security improvements (achieved compliance, mitigated risks)

**Recommended format** (numbered list, each item with bold title + description):
```
1. **[Outcome Name]**: [Verifiable description of the benefit achieved].
2. **[Outcome Name]**: [Verifiable description of the benefit achieved].
```

**If no exact metrics are available**, use:
- Number of accounts/environments/applications connected or protected
- Elimination of a specific risk or problem
- Before vs. after description of the state

## Step 7 — Architecture Diagrams Section

Always include this section indicating:
- Which documents contain the existing diagrams
- Which diagrams should be attached to the form
- If no diagram exists, clearly flag it so the team can create one

## Step 8 — Generate Word Document

Once all fields are drafted, generate a professional `.docx` using `docx-js` with:
- Header with customer name and target SDP
- Each field as a section with a heading title
- AWS services table with color formatting
- Clear and organized dates section
- Footer with customer contact info and ITERA team details
