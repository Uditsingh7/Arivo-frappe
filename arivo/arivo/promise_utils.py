import frappe
from frappe.utils import now_datetime

@frappe.whitelist(allow_guest=True)
def log_promise(invoice_name, promise_date, promise_amount=None, note=None):
    frappe.get_doc({
        "doctype": "AR Promise Log",
        "parenttype": "Sales Invoice",
        "parentfield": "ar_promise_log",
        "parent": invoice_name,
        "promise_date": promise_date,
        "promise_amount": promise_amount or 0,
        "promise_status": "Pending",
        "noted_by": frappe.session.user,
        "noted_on": now_datetime(),
        "note": note or ""
    }).insert(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "success", "message": f"Promise logged for {promise_date}"}

@frappe.whitelist(allow_guest=True)
def get_promise_status(invoice_name):
    promises = frappe.get_all(
        "AR Promise Log",
        filters={"parent": invoice_name, "parenttype": "Sales Invoice"},
        fields=["promise_date", "promise_amount", "promise_status", "noted_by"],
        order_by="noted_on desc",
        limit=1
    )
    return promises[0] if promises else None

def update_broken_promises(allow_guest=True):
    today = frappe.utils.today()
    broken = frappe.get_all(
        "AR Promise Log",
        filters={"promise_status": "Pending", "promise_date": ["<", today]},
        fields=["name"]
    )
    for p in broken:
        frappe.db.set_value("AR Promise Log", p.name, "promise_status", "Broken")
    frappe.db.commit()
