#!/usr/bin/env python3
"""update_change.py — Step 5 of the Golden Pattern (Track B).
Parses the Ansible patch report and updates the ServiceNow Change Request ticket.
Env vars required:
  SNOW_INSTANCE, SNOW_USER, SNOW_PASSWORD, CHANGE_SYS_ID
"""
import os, sys, json, requests
INSTANCE = os.environ["SNOW_INSTANCE"]
AUTH     = (os.environ["SNOW_USER"], os.environ["SNOW_PASSWORD"])
BASE     = f"https://{INSTANCE}.service-now.com/api/now/table"
HEADERS  = {"Accept": "application/json", "Content-Type": "application/json"}
CHANGE_SYS_ID = os.environ["CHANGE_SYS_ID"]
REPORT_PATH   = "patch_report.json"
def main():
    # 1. Check if the report exists (if missing, Ansible failed)
    if not os.path.exists(REPORT_PATH):
        print(f"Ansible patch report file {REPORT_PATH} not found. Handling failure state...")
        notes = (
            "❌ OS Patching Failed\n"
            "=====================\n"
            "Status: Failed\n"
            "Details: Ansible playbook execution failed on the target host.\n"
            "Orchestration Tool: Ansible via GitHub Actions"
        )
        body = {
            "work_notes": notes,
            "state": "3",  # 3 = Closed
            "close_code": "unsuccessful",
            "close_notes": "OS patching failed during Ansible playbook execution."
        }
        r = requests.patch(f"{BASE}/change_request/{CHANGE_SYS_ID}", auth=AUTH, headers=HEADERS, json=body)
        r.raise_for_status()
        print("Updated Change Request with failure notes.")
        sys.exit(1)
    # 2. Read the patch report
    try:
        with open(REPORT_PATH, "r") as f:
            report = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to parse patch report JSON: {e}", file=sys.stderr)
        sys.exit(1)
    # 3. Extract metrics
    packages = report.get("packages_updated", 0)
    reboot   = "Yes" if report.get("reboot_required", False) else "No"
    k_before = report.get("kernel_before", "Unknown")
    k_after  = report.get("kernel_after", "Unknown")
    status   = report.get("status", "Success")
    # 4. Format the work notes markdown
    notes = (
        f"🛠️ OS Patching Compliance Summary\n"
        f"==================================\n"
        f"Status: {status}\n"
        f"Packages Updated: {packages}\n"
        f"Reboot Required: {reboot}\n"
        f"Kernel Before: {k_before}\n"
        f"Kernel After: {k_after}\n"
        f"Orchestration Tool: Ansible via GitHub Actions"
    )
    print(f"Compliance notes to be posted:\n{notes}")
    # 5. Prepare payload to close the Change Request
    body = {
        "work_notes": notes,
        "state": "3",  # 3 = Closed
        "close_code": "successful",
        "close_notes": f"OS patching completed successfully. Status: {status}. Packages updated: {packages}. Reboot required: {reboot}."
    }
    # 6. Send PATCH request to ServiceNow
    r = requests.patch(
        f"{BASE}/change_request/{CHANGE_SYS_ID}",
        auth=AUTH, headers=HEADERS,
        json=body
    )
    r.raise_for_status()
    print(f"Successfully closed ServiceNow Change Request {CHANGE_SYS_ID}")
if __name__ == "__main__":
    main()
