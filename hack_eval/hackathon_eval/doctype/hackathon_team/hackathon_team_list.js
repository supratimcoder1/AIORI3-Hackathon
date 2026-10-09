frappe.listview_settings['Hackathon Team'] = {
    hide_name_filter: true,
    hide_name_column: true,
    add_fields: ['team_code', 'status', 'current_level', 'cumulative_score', 'valid_composition', 'problem_statement_area', 'evaluation_decision'],
    
    onload(listview) {
        frappe.listview_settings['Hackathon Team'].patch_listview(listview);
        frappe.listview_settings['Hackathon Team'].bind_events(listview);
    },

    before_render() {
        const listview = frappe.get_list_view('Hackathon Team');
        if (listview) {
            frappe.listview_settings['Hackathon Team'].patch_listview(listview);
            frappe.listview_settings['Hackathon Team'].bind_events(listview);
        }
    },

    bind_events(listview) {
        if (!listview || !listview.wrapper) return;
        
        listview.wrapper.off('.eval_decision')
            .on('click.eval_decision mousedown.eval_decision mouseup.eval_decision pointerdown.eval_decision keydown.eval_decision', '.eval-decision-select, .eval-select-wrapper', function(e) {
                e.stopPropagation();
            })
            .on('change.eval_decision', '.eval-decision-select', function(e) {
                e.preventDefault();
                e.stopPropagation();
                let team_name = $(this).attr('data-team') || $(this).data('team');
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
    },

    patch_listview(listview) {
        if (!listview || !listview.columns) return;

        if (!listview.list_view_settings) {
            listview.list_view_settings = {};
        }
        listview.list_view_settings.total_fields = 12;

        // Ensure user settings don't drop any of the required fields
        let user_settings = frappe.get_user_settings('Hackathon Team');
        if (user_settings && user_settings.fields) {
            ['team_code', 'problem_statement_area', 'cumulative_score', 'evaluation_decision'].forEach(f => {
                if (!user_settings.fields.includes(f)) {
                    user_settings.fields.push(f);
                }
            });
        }

        const ensure_column = (fieldname, label, fieldtype, after_fieldname) => {
            const exists = listview.columns.some(col => col.df && col.df.fieldname === fieldname);
            if (!exists) {
                const df = frappe.meta.get_docfield('Hackathon Team', fieldname) || {
                    fieldname: fieldname,
                    label: __(label),
                    fieldtype: fieldtype
                };
                const new_col = { type: 'Field', df: df };
                
                let target_idx = -1;
                if (after_fieldname) {
                    target_idx = listview.columns.findIndex(col => 
                        (col.type === after_fieldname) || (col.df && col.df.fieldname === after_fieldname)
                    );
                }
                if (target_idx !== -1) {
                    listview.columns.splice(target_idx + 1, 0, new_col);
                } else {
                    listview.columns.push(new_col);
                }
            }
        };

        ensure_column('team_code', 'Team Code', 'Data', 'Status');
        ensure_column('problem_statement_area', 'Problem Statement Area', 'Data', 'team_code');
        ensure_column('cumulative_score', 'Average Score', 'Float', 'problem_statement_area');
        ensure_column('evaluation_decision', 'Evaluate', 'Select', 'cumulative_score');

        if (listview.$result && listview.$result.find('.list-row-head').length) {
            listview.render_header(true);
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
                <div class="eval-select-wrapper" onclick="event.stopPropagation();" onmousedown="event.stopPropagation();" onmouseup="event.stopPropagation();" style="display:inline-block;">
                    <select class="form-control input-xs eval-decision-select" 
                            onclick="event.stopPropagation();" 
                            onmousedown="event.stopPropagation();" 
                            onmouseup="event.stopPropagation();" 
                            onkeydown="event.stopPropagation();" 
                            data-team="${frappe.utils.escape_html(doc.name)}" 
                            style="height: 24px; padding: 1px 4px; font-size: 11px; width: 100px; border-radius: 4px; font-weight: 600; cursor: pointer; ${color_style}">
                        <option value="" ${none_selected}>-- Select --</option>
                        <option value="Level Up" ${level_up_selected}>Level Up</option>
                        <option value="Eliminate" ${eliminate_selected}>Eliminate</option>
                    </select>
                </div>
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
