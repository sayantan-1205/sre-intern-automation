#!/usr/bin/env python3
"""update_servicenow.py — Step 5 of the Golden Pattern.
After Terraform provisions the VM, this:
  1. Creates a CMDB CI in cmdb_ci_vm_instance.
  2. Adds work notes to the RITM and moves it to a closed state.
Env vars required:
  SNOW_INSTANCE, SNOW_USER, SNOW_PASSWORD,
  RITM_SYS_ID, VM_NAME, VM_IP, VM_SIZE, VM_LOCATION
"""
import os
import sys
import requests
INSTANCE = os.environ["SNOW_INSTANCE"]
AUTH = (os.environ["SNOW_USER"], os.environ["SNOW_PASSWORD"])
BASE = f"https://{INSTANCE}.service-now.com/api/now/table"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
RITM_SYS_ID = os.environ["RITM_SYS_ID"]
VM_NAME = os.environ["VM_NAME"]
VM_IP = os.environ.get("VM_IP", "")
VM_SIZE = os.environ.get("VM_SIZE", "")
VM_LOCATION = os.environ.get("VM_LOCATION", "")
def create_ci():
    """Create (or note) a Virtual Machine Instance CI in the CMDB."""
    body = {
        "name": VM_NAME,
        "ip_address": VM_IP,
        "short_description": f"Provisioned via training pipeline ({VM_SIZE} in {VM_LOCATION})",
        "operational_status": "1",  # 1 = Operational
    }
    r = requests.post(f"{BASE}/cmdb_ci_vm_instance", auth=AUTH, headers=HEADERS, json=body)
    r.raise_for_status()
    ci = r.json()["result"]
    print(f"Created CMDB CI: {ci.get('sys_id')} ({VM_NAME})")
    return ci
def close_ritm():
    """Add work notes and move the RITM to Closed Complete (state 3)."""
    notes = (
        f"✅ VM provisioned automatically.\n"
        f"Name: {VM_NAME}\nPrivate IP: {VM_IP}\nSize: {VM_SIZE}\nRegion: {VM_LOCATION}\n"
        f"CMDB CI created. Pipeline: GitHub Actions."
    )
    body = {
        "work_notes": notes,
        "state": "3",  # 3 = Closed Complete (RITM). Confirm the value on your PDI.
        # Note: do NOT set 'stage' directly — it's workflow-managed and setting it can
        # interfere with closure. Setting state + work_notes is the reliable approach.
    }
    r = requests.patch(f"{BASE}/sc_req_item/{RITM_SYS_ID}", auth=AUTH, headers=HEADERS, json=body)
    r.raise_for_status()
    print(f"Updated + closed RITM {RITM_SYS_ID}")
def main():
    try:
        create_ci()
        close_ritm()
    except requests.HTTPError as e:
        print(f"ServiceNow API error: {e}\n{e.response.text}", file=sys.stderr)
        sys.exit(1)
if __name__ == "__main__":
    main()
