import frappe
import json

def run():
    ws_path = "/mnt/d/Projects/AIORI3-Hackathon/frappe-bench/apps/hack_eval/hack_eval/hackathon_eval/workspace/hackathon_control_center/hackathon_control_center.json"
    with open(ws_path, "r") as f:
        data = json.load(f)
    
    ws = frappe.get_doc("Workspace", "Hackathon Control Center")
    ws.update(data)
    ws.flags.ignore_permissions = True
    ws.save()
    frappe.db.commit()
    frappe.clear_cache()
    print("Workspace synced and cache cleared.")
