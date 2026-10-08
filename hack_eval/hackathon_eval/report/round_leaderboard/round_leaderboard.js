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
		
		if (column.fieldname == "team") {
			value = `<a href="/app/query-report/Team Scorecard?team=${encodeURIComponent(data.team)}" target="_blank">${data.team}</a>`;
		}

		if (data && data.flag_incomplete && column.fieldname == "flag_incomplete") {
			value = "<span style='color:red'>" + value + "</span>";
		}
		if (data && data.flag_disagreement && column.fieldname == "flag_disagreement") {
			value = "<span style='color:orange'>" + value + "</span>";
		}
		if (data && data.flag_near_cutoff && column.fieldname == "flag_near_cutoff") {
			value = "<span style='color:blue'>" + value + "</span>";
		}
		if (data && data.flag_tie_at_cutoff && column.fieldname == "flag_tie_at_cutoff") {
			value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
		}

		return value;
	}
};
