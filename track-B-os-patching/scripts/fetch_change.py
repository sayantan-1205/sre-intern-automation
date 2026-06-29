#!/usr/bin/env python3
"""fetch_change.py — Step 3 of the Golden Pattern (Track B).
Reads Change Request details from ServiceNow, resolves the target IP,
and writes the Ansible inventory.ini.
Env vars required:
  SNOW_INSTANCE, SNOW_USER, SNOW_PASSWORD, CHANGE_NUMBER
"""
import os, sys, requests, re
INSTANCE = os.environ["SNOW_INSTANCE"]
AUTH     = (os.environ["SNOW_USER"], os.environ["SNOW_PASSWORD"])
BASE     = f"https://{INSTANCE}.service-now.com/api/now/table"
HEADERS  = {"Accept": "application/json"}
CHANGE_NUMBER = os.environ["CHANGE_NUMBER"]
# 1. Fetch Change Request details
r = requests.get(
    f"{BASE}/change_request",
    auth=AUTH, headers=HEADERS,
    params={"sysparm_query": f"number={CHANGE_NUMBER}",
            "sysparm_fields": "sys_id,cmdb_ci,description,short_description",
            "sysparm_limit": 1}
)
r.raise_for_status()
results = r.json()["result"]
if not results:
    print(f"ERROR: Change Request {CHANGE_NUMBER} not found.", file=sys.stderr)
    sys.exit(1)
change = results[0]
change_sys_id = change["sys_id"]
cmdb_ci = change.get("cmdb_ci")
description = change.get("description", "")
target_ip = ""
vm_name = ""
# 2. Try to get IP from the CMDB CI
if cmdb_ci and isinstance(cmdb_ci, dict) and cmdb_ci.get("value"):
    ci_sys_id = cmdb_ci["value"]
    print(f"Found related CMDB CI sys_id: {ci_sys_id}. Querying for IP address...")
    r_ci = requests.get(
        f"{BASE}/cmdb_ci_vm_instance/{ci_sys_id}",
        auth=AUTH, headers=HEADERS,
        params={"sysparm_fields": "name,ip_address"}
    )
    if r_ci.status_code == 200 and r_ci.json().get("result"):
        ci_data = r_ci.json()["result"]
        target_ip = ci_data.get("ip_address", "")
        vm_name = ci_data.get("name", "")
        print(f"Resolved CI Name: {vm_name} | IP: {target_ip}")
    else:
        # Fallback to generic cmdb_ci table if not in vm_instance
        r_ci2 = requests.get(
            f"{BASE}/cmdb_ci/{ci_sys_id}",
            auth=AUTH, headers=HEADERS,
            params={"sysparm_fields": "name,ip_address"}
        )
        if r_ci2.status_code == 200 and r_ci2.json().get("result"):
            ci_data = r_ci2.json()["result"]
            target_ip = ci_data.get("ip_address", "")
            vm_name = ci_data.get("name", "")
            print(f"Resolved Generic CI Name: {vm_name} | IP: {target_ip}")
# 3. Fallback: Parse description/short_description for IP
if not target_ip:
    print("CMDB CI IP not found. Attempting to parse IP from Change Request description...")
    # Simple regex to search for an IPv4 address
    ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', description)
    if ip_match:
        target_ip = ip_match.group(0)
        print(f"Found IP in description: {target_ip}")
    else:
        # Check short_description
        short_desc = change.get("short_description", "")
        ip_match_sd = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', short_desc)
        if ip_match_sd:
            target_ip = ip_match_sd.group(0)
            print(f"Found IP in short_description: {target_ip}")
if not target_ip:
    print("ERROR: Could not resolve target IP from CMDB CI or Description.", file=sys.stderr)
    sys.exit(1)
if not vm_name:
    vm_name = f"vm-{CHANGE_NUMBER.lower()}"
print(f"Resolved Target IP: {target_ip} for VM: {vm_name}")
# Write inventory.ini for Ansible
inventory_content = f"""[targets]
{target_ip} ansible_user=azureuser ansible_ssh_private_key_file=../private_key.pem
"""
with open("ansible/inventory.ini", "w") as f:
    f.write(inventory_content)
print("Generated ansible/inventory.ini")
# Write step outputs for GitHub Actions
github_output = os.environ.get("GITHUB_OUTPUT")
if github_output:
    with open(github_output, "a") as f:
        f.write(f"change_sys_id={change_sys_id}\n")
        f.write(f"target_ip={target_ip}\n")
        f.write(f"vm_name={vm_name}\n")
else:
    print("GITHUB_OUTPUT not set. Skipping step outputs.")
