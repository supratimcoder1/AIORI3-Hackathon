import frappe
import json
import os

def execute():
    # 1. Force sync Mentor Profile JSON
    mentor_profile_path = "/mnt/d/Projects/AIORI3-Hackathon/frappe-bench/apps/hack_eval/hack_eval/hackathon_eval/doctype/mentor_profile/mentor_profile.json"
    with open(mentor_profile_path, "r") as f:
        data2 = json.load(f)
    if frappe.db.exists("DocType", "Mentor Profile"):
        dt = frappe.get_doc("DocType", "Mentor Profile")
        dt.update(data2)
        dt.flags.ignore_permissions = True
        dt.save()
    else:
        dt = frappe.get_doc(data2)
        dt.flags.ignore_permissions = True
        dt.insert()
        
    # 2. Force sync Workspace
    workspace_path = "/mnt/d/Projects/AIORI3-Hackathon/frappe-bench/apps/hack_eval/hack_eval/hackathon_eval/workspace/hackathon_control_center/hackathon_control_center.json"
    with open(workspace_path, "r") as f:
        data = json.load(f)
        
    if frappe.db.exists("Workspace", "Hackathon Control Center"):
        ws = frappe.get_doc("Workspace", "Hackathon Control Center")
        ws.update(data)
        ws.flags.ignore_permissions = True
        ws.save()
    else:
        ws = frappe.get_doc(data)
        ws.flags.ignore_permissions = True
        ws.insert()
    print("Workspace synced.")
    
    frappe.db.commit()
    print("DocType synced.")

if __name__ == "__main__":
    frappe.init(site="localhost:8000")
    frappe.connect()
    execute()
    frappe.destroy()
