import frappe

def run():
    workspaces = ['Users', 'Website', 'Tools', 'Integrations', 'Build']
    for w in workspaces:
        if frappe.db.exists('Workspace', w):
            doc = frappe.get_doc('Workspace', w)
            doc.public = 0
            doc.save(ignore_permissions=True)
    frappe.db.commit()
    print("Workspaces hidden")
