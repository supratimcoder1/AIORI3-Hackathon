// Copyright (c) 2026, AIORI and contributors
// For license information, please see license.txt

frappe.query_reports["Team Evaluations"] = {
	"filters": [
		{
			"fieldname": "round",
			"label": __("Round"),
			"fieldtype": "Link",
			"options": "Hackathon Round"
		},
		{
			"fieldname": "track",
			"label": __("Track"),
			"fieldtype": "Select",
			"options": "\nInternet Measurements\nCyber Security\nCloud Computing & IOT\n6G & Future Networks\nSmart Cities"
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (data && column.fieldname === "team_link") {
			const label = data.team_link || data.team_name;
			value = `<a href="/app/evaluation?team=${encodeURIComponent(data.team_link)}" target="_blank" style="font-weight:bold">${frappe.utils.escape_html(label)}</a>`;
		}

		return value;
	}
};
