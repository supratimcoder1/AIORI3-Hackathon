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
		
		if (data && column.fieldname === "team_code") {
			const label = data.team_code || data.team_name || data.team_link;
			value = `<span style="font-weight:600; cursor:default; pointer-events:none;">${frappe.utils.escape_html(label)}</span>`;
		}

		if (data && column.fieldname === "team_name") {
			value = `<span style="cursor:default; pointer-events:none;">${frappe.utils.escape_html(value || '')}</span>`;
		}

		if (data && column.fieldname === "valid") {
			if (data.valid === "Valid" || data.valid === 1) {
				value = `<span class="indicator-pill green bold">Valid</span>`;
			} else {
				value = `<span class="indicator-pill red bold">Invalid</span>`;
			}
		}

		return value;
	}
};
