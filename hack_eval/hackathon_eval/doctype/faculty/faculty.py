import frappe
from frappe.model.document import Document

class Faculty(Document):
    def before_save(self):
        if self.email:
            self.email = self.email.lower().strip()
