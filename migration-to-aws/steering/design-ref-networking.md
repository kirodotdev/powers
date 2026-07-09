# Networking Mappings

## google_compute_network

**Purpose:** Virtual private cloud network

**Default:** aws_vpc (VPC)

**Candidates:**
- aws_vpc

**Signals:** None — direct 1:1 mapping.

**Eliminators:** None

**Peek at secondaries:** No

**1:Many Expansion:**

A GCP VPC always expands to multiple AWS resources:
- aws_vpc — primary
- aws_internet_gateway — GCP VPCs have implicit internet access, AWS requires explicit IGW
- aws_route_table — at least one for public subnets
- aws_route — default route to IGW

**Note on subnets:** GCP VPC subnets are separate resources (google_compute_subnetwork). On AWS, you typically need subnets in at least 2 AZs for services like RDS and ECS. The number of AWS subnets may exceed the number of GCP subnets. This is handled in the secondary mapping for google_compute_subnetwork.

**Source Config to Carry Forward:**
- name — determines VPC name (becomes VPC tag or resource identifier)
- auto_create_subnetworks — if true, GCP auto-creates subnets in every region. AWS doesn't have this concept; subnets must be explicit.
- routing_mode — REGIONAL is standard (AWS VPCs are regional by nature). GLOBAL has no AWS equivalent.

---

## google_compute_subnetwork

**Purpose:** Subnet within a VPC network

**Default:** aws_subnet

**Candidates:**
- aws_subnet

**Signals:** None — direct 1:1 mapping.

**Eliminators:** None

**Peek at secondaries:** No

**1:Many Expansion:**
- aws_subnet — primary
- aws_route_table — if custom routes defined
- aws_network_acl — if custom access control needed

**Source Config to Carry Forward:**
- name — determines subnet name
- ip_cidr_range — determines CIDR block
- region — determines AWS region (mapped from GCP region)
- network — determines VPC association (resolved from google_compute_network mapping)
- private_ip_google_access — determines DNS hostname type
- log_config — determines VPC Flow Logs configuration

---

## google_compute_address (Static IP)

**Purpose:** Static external IP address

**Default:** aws_eip (Elastic IP) or aws_internet_gateway (if network-level)

**Candidates:**
- aws_eip — for instance-level static IP
- aws_internet_gateway — for network NAT

**Signals:**

| Config Field | Value | Favors | Weight | Reason |
|---|---|---|---|---|
| address_type | INTERNAL | aws_network_interface | moderate | Internal static IP |
| address_type | EXTERNAL | aws_eip | strong | External static IP |
| purpose | NAT | aws_nat_gateway | strong | NAT gateway for outbound NAT |
| purpose | GCE_ENDPOINT | aws_network_interface | moderate | Instance endpoint |
| network_tier | PREMIUM | aws_eip | moderate | Premium tier maps to standard EIP |
| network_tier | STANDARD | aws_eip | weak | Standard tier may have performance implications |

**Eliminators:** None

**Peek at secondaries:** No

**1:Many Expansion (EIP):**
- aws_eip — primary
- aws_eip_association — if associated to instance

**1:Many Expansion (NAT Gateway):**
- aws_nat_gateway — primary
- aws_eip — elastic IP for NAT gateway
- aws_route — for NAT routing

**Source Config to Carry Forward:**
- address_type — determines EIP or NAT gateway type
- region — determines AWS region
- network — determines VPC (resolved from google_compute_network mapping)

---

## google_compute_forwarding_rule (Load Balancer)

**Purpose:** Load balancing and traffic forwarding

**Default:** aws_lb (Load Balancer) - ALB or NLB depending on protocol

**Candidates:**
- aws_lb with type = "application" (ALB for HTTP/HTTPS)
- aws_lb with type = "network" (NLB for TCP/UDP)

**Signals:**

| Config Field | Value | Favors | Weight | Reason |
|---|---|---|---|---|
| load_balancing_scheme | EXTERNAL | aws_lb | strong | Public load balancer |
| load_balancing_scheme | INTERNAL | aws_lb with internal=true | moderate | Internal load balancer |
| ip_protocol | TCP | aws_lb type network | strong | NLB for TCP |
| ip_protocol | UDP | aws_lb type network | strong | NLB for UDP |
| ip_protocol | HTTP | aws_lb type application | strong | ALB for HTTP |
| ip_protocol | HTTPS | aws_lb type application | strong | ALB for HTTPS |
| ports | 80, 443 | aws_lb type application | strong | ALB for web traffic |
| ports | 3306, 5432 | aws_lb type network | strong | NLB for database traffic |
| all_ports | true | aws_lb type network | strong | NLB for all ports (passthrough) |

**Eliminators:** None

**Peek at secondaries:** Yes — must check google_backend_service and google_target_pool resources

**1:Many Expansion (ALB - Application Load Balancer):**
- aws_lb with type = "application"
- aws_lb_listener — one per port/protocol
- aws_lb_target_group — one per backend service
- aws_lb_listener_rule — for path/host-based routing
- aws_security_group — for ALB ingress rules

**1:Many Expansion (NLB - Network Load Balancer):**
- aws_lb with type = "network"
- aws_lb_listener — one per port/protocol
- aws_lb_target_group — one per backend service
- aws_security_group — for NLB ingress rules (if using security groups)

**Source Config to Carry Forward:**
- name — determines load balancer name
- ip_protocol — determines ALB vs NLB
- ports — determines listener ports
- load_balancing_scheme — determines internal vs external
- region — determines AWS region
- network / subnetwork — determines VPC and subnet placement

---

## Secondary: google_compute_subnetwork

**Behavior:** Subnets are network_path secondaries that define which subnets exist within a VPC. Each subnet maps to an AWS subnet.

**Mapping Behavior:**

When google_compute_network maps to:
- aws_vpc → Each google_compute_subnetwork becomes a separate aws_subnet

**Implementation Notes:**
1. GCP subnet CIDR range carries forward to aws_subnet cidr_block
2. GCP subnet region determines AWS availability zone (may need adjustment for multi-AZ)
3. Each subnet gets a route table association
4. **Important:** AWS typically requires subnets in at least 2 AZs for HA services (RDS, ECS)
   - If GCP has 1 subnet, create 2-3 AWS subnets across AZs
   - This may result in MORE AWS subnets than GCP subnets
5. Private IP Google Access (GCP) → DNS hostname type on AWS subnet
6. VPC Flow Logs configuration → aws_flow_log resource

**Skip Condition:**
If the primary google_compute_network is skipped, skip these secondaries. However, AWS requires at least one subnet, so plan accordingly.

---

## Secondary: google_compute_firewall

**Behavior:** Firewalls are network_path secondaries that define network access control rules. They map to AWS security groups.

**Mapping Behavior:**

When firewall serves compute resource:
- Firewall rules become aws_security_group with ingress/egress rules attached to compute resources

When firewall serves network resource:
- Becomes aws_security_group that can be referenced by multiple compute resources

**Rule Translation:**
- GCP firewall `allow` rules → aws_security_group ingress rules
- GCP firewall `deny` rules → aws_security_group deny rules (or use separate deny policy)
- GCP firewall `sourceRanges` → security group CIDR blocks
- GCP firewall `targetTags` → security group resource associations (EC2 tags)
- GCP firewall ports/protocols → security group port/protocol specifications

**Implementation Notes:**
1. Firewall direction (ingress/egress) must be explicitly set in AWS security groups
2. GCP has implicit default allow; AWS is implicit deny
3. Stateful rules: GCP firewalls are stateful, AWS security groups are stateful
4. Named ranges and service accounts in rules must be expanded to actual IPs/IDs
5. Multiple rules may need to be combined into single security group

**Skip Condition:**
If the primary compute resource is skipped, firewall rules can be skipped. Otherwise, create security group for access control.

---

## Cloud Interconnect

**Purpose:** Dedicated/partner connectivity between on-premises and cloud

**Default:** AWS Direct Connect

**Rationale for default:** Direct Connect is the 1:1 equivalent for dedicated enterprise connectivity. For development or temporary migration needs, Site-to-Site VPN is a faster, lower-cost alternative.

**Candidates:**
- AWS Direct Connect — dedicated connection, lowest latency, highest bandwidth
- AWS Site-to-Site VPN — encrypted tunnel over public internet, quicker setup

**Signals:**

| Signal | Favors | Weight | Reason |
|---|---|---|---|
| Dedicated interconnect (10/100 Gbps) | Direct Connect | strong | Requires dedicated fiber; 6+ months setup |
| Partner interconnect | Direct Connect (hosted) | moderate | Partner-facilitated, faster setup |
| Development/temporary connectivity | Site-to-Site VPN | strong | Quicker, lower cost, sufficient for migration |
| Compliance (PCI, HIPAA, FedRAMP) | Direct Connect | strong | Explicit data path required |

**Migration Notes:**
- Direct Connect requires physical provisioning (plan 2-6 months lead time)
- During migration, use Site-to-Site VPN as temporary bridge
- BGP configuration must be adapted from GCP Cloud Router to AWS VGW/TGW
