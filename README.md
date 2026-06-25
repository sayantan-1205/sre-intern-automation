# Track A — VM Provisioning via ServiceNow (End-to-End Automation)

This repository contains the complete infrastructure-as-code (IaC) and integration glue for **Track A: VM Provisioning via ServiceNow**. It implements the **Golden Pattern**: ordering a virtual machine in ServiceNow, triggering a GitHub Actions pipeline, provisioning resources in Microsoft Azure, updating the ServiceNow Configuration Management Database (CMDB), and auto-closing the request ticket.

---

## 🏗️ Architecture Flow

```mermaid
sequenceDiagram
    actor User as SRE Intern / End User
    participant SNOW as ServiceNow (PDI)
    participant GH as GitHub Actions
    participant Azure as Microsoft Azure
    
    User->>SNOW: Orders "Request a Virtual Machine"
    Note over SNOW: Business Rule captures variables<br/>(Name, Size, Region)
    SNOW->>GH: Outbound REST API call (POST repository_dispatch)
    Note over GH: GitHub Runner spins up
    GH->>SNOW: fetch_request.py (Resolves variables)
    GH->>Azure: terraform apply (Provisions VM, VNet, Subnet, NIC)
    Azure-->>GH: Returns Private IP, Location, Name
    GH->>SNOW: update_servicenow.py (Creates CMDB CI & closes RITM)
    Note over SNOW: CMDB VM Instance logged<br/>Ticket state set to Closed Complete
