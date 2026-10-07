import frappe
import json
def execute():
    perms = frappe.get_all("DocPerm", filters={"parent": "Hackathon Team"}, fields=["role", "create", "write"])
    with open("team_perms.json", "w") as f:
        json.dump(perms, f)
