frappe.listview_settings['Hackathon Team'] = {
    hide_name_filter: true,
    hide_name_column: true,
    add_fields: ['team_code', 'status', 'current_level', 'cumulative_score', 'valid_composition', 'problem_statement_area'],
    get_indicator(doc) {
        if (doc.valid_composition === 0) return [__("Invalid Comp"), "red", "valid_composition,=,0"];
        if (doc.status === "Eliminated") return [__("Eliminated"), "red", "status,=,Eliminated"];
        if (doc.status === "Active") return [__("Active"), "green", "status,=,Active"];
        if (doc.status === "Finalist") return [__("Finalist"), "orange", "status,=,Finalist"];
        if (doc.status === "Winner") return [__("Winner"), "blue", "status,=,Winner"];
    }
};
