import frappe
import json

def run():
    # Frappe v15 uses List View Settings
    settings = frappe.get_all('List View Settings', filters={'name': 'Evaluation'})
    fields_list = [
        {"fieldname":"name"},
        {"fieldname":"team"},
        {"fieldname":"round"},
        {"fieldname":"evaluator"},
        {"fieldname":"status"},
        {"fieldname":"total_score"}
    ]
    if not settings:
        setting = frappe.new_doc('List View Settings')
        setting.name = 'Evaluation'
        setting.disable_count = 0
        setting.disable_sidebar_stats = 0
        setting.fields = json.dumps(fields_list)
        setting.insert(ignore_permissions=True)
    else:
        setting = frappe.get_doc('List View Settings', 'Evaluation')
        setting.fields = json.dumps(fields_list)
        setting.save(ignore_permissions=True)
    
    frappe.db.commit()
    print("List view settings updated.")
