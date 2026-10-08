import frappe
from frappe.model.document import Document
from frappe.utils import flt

class Evaluation(Document):
    def validate(self):
        # 1. Level-gating validation for Mentors
        roles = frappe.get_roles(frappe.session.user)
        is_admin = ("System Manager" in roles or "Hackathon Organizer" in roles or frappe.session.user == "Administrator")
        
        if not is_admin and self.round:
            round_status = frappe.db.get_value("Hackathon Round", self.round, "status")
            if round_status != "Open":
                frappe.throw(f"This round ({self.round}) is currently {round_status}. Evaluations are locked for mentors.")
                
            if not self.is_new():
                old_status = frappe.db.get_value("Evaluation", self.name, "status")
                if old_status == "Submitted":
                    frappe.throw("This evaluation has already been submitted and cannot be modified.")

        # 2. Populate criteria if scores table is empty
        if not self.scores and self.round:
            round_doc = frappe.get_doc("Hackathon Round", self.round)
            for criteria in round_doc.criteria:
                self.append("scores", {
                    "criterion": criteria.criterion,
                    "max_score": flt(criteria.max_score),
                    "score": 0.0
                })
        
        # 3. Calculate total score and validate range [0, max_score]
        total = 0.0
        for row in self.scores:
            score_val = flt(row.score)
            max_val = flt(row.max_score or 10.0)
            if score_val < 0.0:
                frappe.throw(f"Score for {row.criterion} cannot be negative.")
            if score_val > max_val:
                frappe.throw(f"Score for {row.criterion} cannot exceed max score {max_val}.")
            total += score_val
            
        self.total_score = total

    def before_save(self):
        if self.ready_to_submit and self.status != "Submitted":
            # Set to submitted
            self.status = "Submitted"
            self.submitted_on = frappe.utils.now_datetime()
            # Clear the checkbox so it doesn't stay checked if reopened to draft
            self.ready_to_submit = 0

    def on_submit(self):
        self.status = "Submitted"
        self.submitted_on = frappe.utils.now_datetime()
