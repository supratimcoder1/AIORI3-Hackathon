app_name = "hack_eval"
app_title = "Hackathon Eval"
app_publisher = "AIORI"
app_description = "Hackathon Evaluation Platform"
app_email = "test@example.com"
app_license = "mit"

after_install = "hack_eval.setup.after_install"
after_migrate = "hack_eval.setup.after_migrate"

permission_query_conditions = {
    "Hackathon Team": "hack_eval.hackathon_eval.permissions.get_team_permission_query",
    "Evaluation": "hack_eval.hackathon_eval.permissions.get_evaluation_permission_query",
}

doctype_js = {
    "User": "public/js/user_custom.js"
}

has_permission = {
    "Hackathon Team": "hack_eval.hackathon_eval.permissions.team_has_permission",
    "Evaluation": "hack_eval.hackathon_eval.permissions.evaluation_has_permission",
}

doc_events = {
    "User": {
        "before_insert": "hack_eval.hackathon_eval.permissions.generate_user_uuid"
    }
}

boot_session = "hack_eval.hackathon_eval.boot.boot_session"

before_request = ["hack_eval.hackathon_eval.evaluation_logic.sanitize_request_params"]

app_include_js = "/assets/hack_eval/js/hack_eval.js"

fixtures = []
