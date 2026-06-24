# Validation Checklist — Before Submitting to AWS

Run this full validation before submitting any customer reference to the APN portal.

---

## Content Validation

### Mandatory fields
- [ ] **Case name** is complete and mentions the AWS services of the target SDP
- [ ] **Customer challenge** has at least 3 paragraphs and describes a real, specific problem
- [ ] **Proposed solution** describes the architecture component by component
- [ ] **AWS services table** is included with the specific role of each service
- [ ] **Third parties/ISVs** are listed (or explicitly stated as not applicable)
- [ ] **All three dates** are complete: start, end, production
- [ ] **Outcomes** include at least 3 documented results
- [ ] **Diagrams** are identified and ready to attach

### Content quality
- [ ] The challenge does NOT mention the partner/implementer
- [ ] The solution names AWS services with their exact and complete names
- [ ] Dates are consistent: start ≤ end ≤ production
- [ ] Outcomes are verifiable by the customer (not fabricated)
- [ ] At least one AWS Account ID of the customer is included
- [ ] Language is professional and can be understood without internal context

---

## Technical Validation

### AWS Services
- [ ] Listed services correspond to the SDP being applied for
- [ ] Services are in production (not just planned or in development)
- [ ] Mentioned Account IDs are correct for the customer

### For Networking SDP specifically:
- [ ] At least one of the following is mentioned: Transit Gateway, Direct Connect, Site-to-Site VPN
- [ ] Amazon VPC is mentioned with subnet configuration
- [ ] If WAF: number of rules and Web ACLs is specified
- [ ] If CloudFront: origin configuration is mentioned (S3 or ALB)
- [ ] If Route 53: DNS role in the solution is described

---

## Date Validation

| Check | OK? |
|---|---|
| Start date ≤ end date | [ ] |
| End date ≤ production date (or equal) | [ ] |
| Project is already in production (not planned) | [ ] |
| Dates match supporting documents (closure reports, proposals) | [ ] |
| If sub-projects exist, all dates are consistent | [ ] |

---

## Diagram Validation

- [ ] At least one architecture diagram is ready to attach
- [ ] The diagram shows all AWS services mentioned in the case
- [ ] The diagram is in PNG, JPG, or PDF format
- [ ] The diagram is readable (not too small or compressed)
- [ ] If multiple AWS accounts exist, the diagram clearly distinguishes them

**If no diagram exists**: STOP — do not submit until one is available. It is a mandatory requirement.

---

## Customer Validation

- [ ] A customer contact is identified who can validate the case with AWS
- [ ] The contact has a relevant title (IT Manager, Architect, CTO, etc.)
- [ ] The customer has agreed to be referenced publicly (or privately)
- [ ] Customer data (name, Account ID, industry) is correct

---

## Final Submission Validation

- [ ] The Word document is complete and well formatted
- [ ] The architecture diagram is attached as a separate file
- [ ] Customer contact details are ready for the APN form
- [ ] The target SDP has the minimum required services
- [ ] Spelling and professional writing have been reviewed

---

## Red Flags (do not submit if any of these apply)

- Production dates in the future
- No architecture diagram
- Outcomes the customer could not confirm
- Incorrect or fictitious Account IDs
- AWS services not yet in production
- No customer contact identified for AWS validation
- The case mixes services from multiple SDPs without a clear focus

---

## Supporting Documents to Keep on File

Save these alongside the case study in case AWS requests evidence:

1. Customer-signed closure report
2. Accepted economic proposal or SOW
3. Technical spec / Architecture requirements document
4. AWS console screenshots showing deployed services
5. Architecture diagram in editable format (draw.io, Lucidchart)
