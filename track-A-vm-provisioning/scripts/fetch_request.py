#!/usr/bin/env python3
"""fetch_request.py — Step 3 of the Golden Pattern.
Reads RITM variable values from ServiceNow and writes them as
GitHub Actions step outputs (and as terraform.tfvars for Terraform).
Env vars required:
  SNOW_INSTANCE, SNOW_USER, SNOW_PASSWORD, RITM_NUMBER
Optional (passed in client_payload for push trigger — skip API query if present):
  VM_NAME, VM_SIZE, REGION
"""
import os, sys, requests
INSTANCE = os.environ["SNOW_INSTANCE"]
AUTH     = (os.environ["SNOW_USER"], os.environ["SNOW_PASSWORD"])
BASE     = f"https://{INSTANCE}.service-now.com/api/now/table"
HEADERS  = {"Accept": "application/json"}
RITM_NUMBER = os.environ["RITM_NUMBER"]
# --- Try payload values first (push trigger passes these directly) ---
vm_name = os.environ.get("VM_NAME", "").strip()
vm_size = os.environ.get("VM_SIZE", "").strip()
region  = os.environ.get("REGION",  "").strip()
def fetch_from_snow():
    """Fall back: query ServiceNow for the RITM's catalog variable values."""
    global vm_name, vm_size, region
    # 1. Get the RITM sys_id and request sys_id
    r = requests.get(
        f"{BASE}/sc_req_item",
        auth=AUTH, headers=HEADERS,
        params={"sysparm_query": f"number={RITM_NUMBER}",
                "sysparm_fields": "sys_id,request",
                "sysparm_limit": 1}
    )
    r.raise_for_status()
    results = r.json()["result"]
    if not results:
        print(f"ERROR: RITM {RITM_NUMBER} not found.", file=sys.stderr)
        sys.exit(1)
    ritm = results[0]
    ritm_sys_id = ritm["sys_id"]
    # 2. Get catalog variable values via sc_item_option_mtom
    r2 = requests.get(
        f"{BASE}/sc_item_option_mtom",
        auth=AUTH, headers=HEADERS,
        params={"sysparm_query": f"request_item={ritm_sys_id}",
                "sysparm_fields": "sc_item_option.item_option_new.name,sc_item_option.value",
                "sysparm_limit": 20}
    )
    r2.raise_for_status()
    vars_raw = r2.json()["result"]
    var_map = {}
    for v in vars_raw:
        name  = v.get("sc_item_option.item_option_new.name", "")
        value = v.get("sc_item_option.value", "")
        if name:
            var_map[name] = value
    print(f"Variables from SNOW: {var_map}")
    return (
        var_map.get("vm_name", f"vm-{RITM_NUMBER.lower()}"),
        var_map.get("vm_size", "Standard_B1s"),
        var_map.get("region",  "centralindia"),
        ritm_sys_id
    )
def get_ritm_sys_id():
    r = requests.get(
        f"{BASE}/sc_req_item",
        auth=AUTH, headers=HEADERS,
        params={"sysparm_query": f"number={RITM_NUMBER}",
                "sysparm_fields": "sys_id",
                "sysparm_limit": 1}
    )
    r.raise_for_status()
    results = r.json()["result"]
    if not results:
        print(f"ERROR: RITM {RITM_NUMBER} not found.", file=sys.stderr)
        sys.exit(1)
    return results[0]["sys_id"]
try:
    if vm_name and vm_size and region:
        # Push trigger: values already in env — just fetch sys_id
        print("Using values from client_payload.")
        ritm_sys_id = get_ritm_sys_id()
    else:
        # Poll trigger or manual run: query SNOW for variable values
        print("Fetching variable values from ServiceNow...")
        vm_name, vm_size, region, ritm_sys_id = fetch_from_snow()
    # Sanitise vm_name (Azure names: alphanumeric + hyphens, max 15 chars for Windows)
    vm_name = vm_name.strip().lower().replace(" ", "-")[:15] or f"vm-{RITM_NUMBER[-6:].lower()}"
    print(f"RITM: {RITM_NUMBER} | VM: {vm_name} | Size: {vm_size} | Region: {region}")
    # Write GitHub Actions step outputs
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"ritm_sys_id={ritm_sys_id}\n")
            f.write(f"vm_name={vm_name}\n")
            f.write(f"vm_size={vm_size}\n")
            f.write(f"region={region}\n")
    else:
        print("GITHUB_OUTPUT not set. Skipping step output generation.")
    # Write terraform.tfvars so Terraform picks up the values
    with open("terraform/terraform.tfvars", "a") as f:
        f.write(f'vm_name = "{vm_name}"\n')
        f.write(f'vm_size = "{vm_size}"\n')
        f.write(f'region  = "{region}"\n')
except requests.HTTPError as e:
    print(f"ServiceNow API error: {e}\n{e.response.text}", file=sys.stderr)
    sys.exit(1)
