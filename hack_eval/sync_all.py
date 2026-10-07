import frappe
import json

def sync_doc(doctype, path):
    with open(path, "r") as f:
        data = json.load(f)
    if frappe.db.exists("DocType", doctype):
        dt = frappe.get_doc("DocType", doctype)
        dt.update(data)
        dt.flags.ignore_permissions = True
        dt.save()
    else:
        dt = frappe.get_doc(data)
        dt.flags.ignore_permissions = True
        dt.insert()
    print(f"Synced {doctype}")

def execute():
    base = "/mnt/d/Projects/AIORI3-Hackathon/frappe-bench/apps/hack_eval/hack_eval/hackathon_eval/doctype/"
    sync_doc("Hackathon Team", base + "hackathon_team/hackathon_team.json")
    sync_doc("Hackathon Round", base + "hackathon_round/hackathon_round.json")
    sync_doc("Evaluation", base + "evaluation/evaluation.json")
    frappe.db.commit()
    print("All DocTypes synced.")

if __name__ == "__main__":
    frappe.init(site="localhost:8000")
    frappe.connect()
    execute()
    frappe.destroy()
