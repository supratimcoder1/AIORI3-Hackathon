import frappe
import json

def run():
    # 1. Update List View Settings for Evaluation
    fields_list = [
        {"fieldname": "name"},
        {"fieldname": "team"},
        {"fieldname": "round"},
        {"fieldname": "evaluator"},
        {"fieldname": "status"},
        {"fieldname": "total_score"}
    ]
    
    if frappe.db.exists("List View Settings", "Evaluation"):
        setting = frappe.get_doc("List View Settings", "Evaluation")
    else:
        setting = frappe.new_doc("List View Settings")
        setting.name = "Evaluation"

    setting.total_fields = "10"
    setting.fields = json.dumps(fields_list)
    setting.save(ignore_permissions=True)

    # 2. Clear any persisted user settings for Evaluation
    frappe.db.sql("""
        DELETE FROM `__UserSettings` 
        WHERE `doctype` = 'Evaluation'
    """)

    # 3. Clear cache
    frappe.cache.delete_keys("user_settings")
    frappe.cache.delete_keys("doctype:Evaluation")
    frappe.db.commit()
    print("Evaluation list view settings and cache successfully updated.")
