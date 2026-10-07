// Copyright (c) 2026, AIORI and contributors
// For license information, please see license.txt

frappe.query_reports["Evaluator Progress"] = {
	"filters": [
		{
			"fieldname": "round",
			"label": __("Round"),
			"fieldtype": "Link",
			"options": "Hackathon Round"
		}
	]
};
