import frappe
from frappe.model.document import Document

class ScoreAdjustment(Document):
    def on_update(self):
        if self.team:
            from hack_eval.hackathon_eval.evaluation_logic import sync_team_scores
            sync_team_scores(self.team)

    def on_trash(self):
        if self.team:
            from hack_eval.hackathon_eval.evaluation_logic import sync_team_scores
            sync_team_scores(self.team)
