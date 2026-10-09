frappe.listview_settings['Hackathon Team'] = {
    hide_name_filter: true,
    hide_name_column: true,
    add_fields: ['team_code', 'status', 'current_level', 'cumulative_score', 'valid_composition', 'problem_statement_area', 'evaluation_decision'],
    
    onload(listview) {
        if (!listview.list_view_settings) {
            listview.list_view_settings = {};
        }
        listview.list_view_settings.total_fields = 10;

        // Attach change listener for Evaluate dropdown
        if (listview.$result && !listview._eval_decision_bound) {
            listview._eval_decision_bound = true;
            listview.$result.on('change', '.eval-decision-select', function(e) {
                e.preventDefault();
                e.stopPropagation();
                let team_name = $(this).data('team');
                let decision = $(this).val();
                let $select = $(this);

                frappe.call({
                    method: 'frappe.client.set_value',
                    args: {
                        doctype: 'Hackathon Team',
                        name: team_name,
                        fieldname: 'evaluation_decision',
                        value: decision
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: __('Team {0} marked as {1}', [team_name, decision || 'Pending']),
                                indicator: decision === 'Level Up' ? 'green' : (decision === 'Eliminate' ? 'red' : 'blue')
                            }, 3);
                            if (decision === 'Level Up') {
                                $select.css({ 'color': '#28a745', 'border-color': '#28a745' });
                            } else if (decision === 'Eliminate') {
                                $select.css({ 'color': '#dc3545', 'border-color': '#dc3545' });
                            } else {
                                $select.css({ 'color': '#6c757d', 'border-color': '#d1d8dd' });
                            }
                        }
                    }
                });
                return false;
            });
        }
    },

    formatters: {
        evaluation_decision(val, df, doc) {
            var is_admin = frappe.user_roles.includes('System Manager') || 
                           frappe.user_roles.includes('Hackathon Organizer') || 
                           frappe.session.user === 'Administrator';

            if (!is_admin) {
                if (val === 'Level Up') return `<span class="indicator-pill green bold">Level Up</span>`;
                if (val === 'Eliminate') return `<span class="indicator-pill red bold">Eliminate</span>`;
                return `<span class="text-muted">-</span>`;
            }

            let level_up_selected = val === 'Level Up' ? 'selected' : '';
            let eliminate_selected = val === 'Eliminate' ? 'selected' : '';
            let none_selected = !val ? 'selected' : '';

            let color_style = val === 'Level Up' ? 'color: #28a745; border-color: #28a745;' : (val === 'Eliminate' ? 'color: #dc3545; border-color: #dc3545;' : 'color: #6c757d; border-color: #d1d8dd;');

            return `
                <select class="form-control input-xs eval-decision-select" data-team="${frappe.utils.escape_html(doc.name)}" style="height: 24px; padding: 1px 4px; font-size: 11px; width: 100px; border-radius: 4px; font-weight: 600; cursor: pointer; ${color_style}">
                    <option value="" ${none_selected}>-- Select --</option>
                    <option value="Level Up" ${level_up_selected}>Level Up</option>
                    <option value="Eliminate" ${eliminate_selected}>Eliminate</option>
                </select>
            `;
        },
        cumulative_score(val, df, doc) {
            let score = flt(val);
            return `<span class="bold" style="color: ${score > 0 ? '#2490ef' : '#888'}; font-size: 12px;">${score.toFixed(3)}</span>`;
        }
    },

    get_indicator(doc) {
        if (doc.valid_composition === 0) return [__("Invalid Comp"), "red", "valid_composition,=,0"];
        if (doc.status === "Eliminated") return [__("Eliminated"), "red", "status,=,Eliminated"];
        if (doc.status === "Active") return [__("Active"), "green", "status,=,Active"];
        if (doc.status === "Finalist") return [__("Finalist"), "orange", "status,=,Finalist"];
        if (doc.status === "Winner") return [__("Winner"), "blue", "status,=,Winner"];
    }
};
