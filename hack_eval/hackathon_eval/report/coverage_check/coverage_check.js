// Copyright (c) 2026, AIORI and contributors
// For license information, please see license.txt

frappe.query_reports["Coverage Check"] = {
	"filters": [
		{
			"fieldname": "round",
			"label": __("Round"),
			"fieldtype": "Link",
			"options": "Hackathon Round",
			"reqd": 1
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname == "status" && data && data.status == "Incomplete") {
			value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
		}
		if (column.fieldname == "status" && data && data.status == "Complete") {
			value = "<span style='color:green'>" + value + "</span>";
		}
		return value;
	}
};
