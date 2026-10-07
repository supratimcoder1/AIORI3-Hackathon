import frappe
from frappe.model.document import Document
from frappe.utils.password import update_password

class MentorProfile(Document):
    def on_update(self):
        # Sync with User DocType
        if not frappe.db.exists("User", self.email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": self.email,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "enabled": 1 if self.status == "Active" else 0,
                "send_welcome_email": 0
            })
            user.append("roles", {"role": self.mentor_role})
            user.insert(ignore_permissions=True)
            # Use canonical Frappe API to set default password and populate __Auth
            update_password(self.email, "Password123")
        else:
            user = frappe.get_doc("User", self.email)
            user.enabled = 1 if self.status == "Active" else 0
            user.first_name = self.first_name
            user.last_name = self.last_name
            
            has_role = False
            for r in user.roles:
                if r.role == self.mentor_role:
                    has_role = True
                    break
            
            if not has_role:
                user.append("roles", {"role": self.mentor_role})
                
            user.save(ignore_permissions=True)
            
    def on_trash(self):
        if frappe.db.exists("User", self.email):
            user = frappe.get_doc("User", self.email)
            user.enabled = 0
            user.save(ignore_permissions=True)
