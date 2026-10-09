frappe.listview_settings['Evaluation'] = {
    hide_name_filter: true,
    add_fields: ['total_score', 'status', 'team_code', 'team_name'],

    formatters: {
        total_score(val, df, doc) {
            let score = val !== undefined && val !== null ? val : 0;
            if (doc.status === 'Submitted') {
                return `<span class="bold text-success">${score}</span>`;
            }
            return `<span class="text-muted">${score}</span>`;
        },
        team_code(val, df, doc) {
            return `<span style="cursor: default; pointer-events: none; font-weight: 500;">${frappe.utils.escape_html(val || '')}</span>`;
        },
        team_name(val, df, doc) {
            return `<span style="cursor: default; pointer-events: none; font-weight: 500;">${frappe.utils.escape_html(val || '')}</span>`;
        }
    },

    onload(listview) {
        frappe.listview_settings['Evaluation'].set_breadcrumbs();
        frappe.listview_settings['Evaluation'].patch_listview(listview);
    },

    before_render() {
        frappe.listview_settings['Evaluation'].set_breadcrumbs();
        const listview = frappe.get_list_view('Evaluation');
        if (listview) {
            frappe.listview_settings['Evaluation'].patch_listview(listview);
        }
    },

    set_breadcrumbs() {
        var is_admin = frappe.user_roles.includes('System Manager') || 
                       frappe.user_roles.includes('Hackathon Organizer') || 
                       frappe.session.user === 'Administrator';

        var target_workspace = is_admin ? "Hackathon Control Center" : "Mentor Dashboard";
        frappe.breadcrumbs.add({
            module: "Hackathon Eval",
            doctype: "Evaluation",
            type: "DocType",
            workspace: target_workspace
        });
    },

    patch_listview(listview) {
        if (!listview || !listview.columns) return;

        // Ensure max fields does not slice out total_score
        if (!listview.list_view_settings) {
            listview.list_view_settings = {};
        }
        listview.list_view_settings.total_fields = 10;

        const has_score = listview.columns.some(col => col.df && col.df.fieldname === 'total_score');
        if (!has_score) {
            const df = frappe.meta.get_docfield('Evaluation', 'total_score') || {
                fieldname: 'total_score',
                label: __('Total Score'),
                fieldtype: 'Float'
            };

            const score_col = {
                type: 'Field',
                df: df
            };

            // Place right after status if status exists
            const status_idx = listview.columns.findIndex(col => 
                col.type === 'Status' || (col.df && col.df.fieldname === 'status')
            );

            if (status_idx !== -1) {
                listview.columns.splice(status_idx + 1, 0, score_col);
            } else {
                listview.columns.push(score_col);
            }

            if (listview.$result && listview.$result.find('.list-row-head').length) {
                listview.render_header(true);
            }
        }
    }
};
