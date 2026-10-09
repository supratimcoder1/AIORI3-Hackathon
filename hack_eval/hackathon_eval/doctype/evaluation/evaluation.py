import frappe
from frappe.model.document import Document
from frappe.utils import flt

class Evaluation(Document):
    def before_insert(self):
        self.populate_team_details()

    def validate(self):
        self.populate_team_details()
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

    def populate_team_details(self):
        if self.team and (not self.team_code or not self.team_name):
            t_data = frappe.db.get_value("Hackathon Team", self.team, ["team_code", "team_name"], as_dict=True)
            if t_data:
                if not self.team_code:
                    self.team_code = t_data.team_code or ""
                if not self.team_name:
                    self.team_name = t_data.team_name or ""

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
        elif not self.ready_to_submit and self.status == "Pending":
            # If they just save without submitting, mark it as Draft to show progress
            self.status = "Draft"

    def on_submit(self):
        self.status = "Submitted"
        self.submitted_on = frappe.utils.now_datetime()
