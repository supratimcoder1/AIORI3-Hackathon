// Copyright (c) 2026, AIORI and contributors
// For license information, please see license.txt

frappe.query_reports["Round Leaderboard"] = {
	"filters": [
		{
			"fieldname": "round",
			"label": __("Round"),
			"fieldtype": "Link",
			"options": "Hackathon Round",
			"reqd": 1
		},
		{
			"fieldname": "track",
			"label": __("Track"),
			"fieldtype": "Select",
			"options": "\nInternet Measurements\nCyber Security\nCloud Computing & IOT\n6G & Future Networks\nSmart Cities",
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (column.fieldname == "team_code") {
			const label = data.team_code || '-';
			value = `<a href="/app/query-report/Team Scorecard?team=${encodeURIComponent(data.team)}" target="_blank" style="font-weight:bold">${frappe.utils.escape_html(label)}</a>`;
		}

		if (data && column.fieldname == "review_status") {
			if (data.review_status === "Completed") {
				value = "<span class='indicator-pill green bold'>Completed</span>";
			} else {
				value = "<span class='indicator-pill orange bold'>Pending</span>";
			}
		}

		if (data && column.fieldname == "outcome") {
			if (data.outcome === "Advanced" || data.outcome === "Finalist" || data.outcome === "Winner") {
				value = "<span class='indicator-pill green bold'>" + frappe.utils.escape_html(data.outcome) + "</span>";
			} else if (data.outcome === "Eliminated") {
				value = "<span class='indicator-pill red bold'>Eliminated</span>";
			} else {
				value = "<span class='text-muted'>Pending</span>";
			}
		}

		return value;
	}
};
