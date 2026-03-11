import frappe

def get_context(context):
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect
