// Copyright (c) 2026, AIORI and contributors
// For license information, please see license.txt

frappe.query_reports["Team Scorecard"] = {
	"filters": [
		{
			"fieldname": "team",
			"label": __("Team"),
			"fieldtype": "Link",
			"options": "Hackathon Team"
		},
		{
			"fieldname": "round",
			"label": __("Round"),
			"fieldtype": "Link",
			"options": "Hackathon Round"
		},
		{
			"fieldname": "evaluator",
			"label": __("Evaluator"),
			"fieldtype": "Link",
			"options": "User"
		}
	]
};
