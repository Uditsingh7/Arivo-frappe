import frappe
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def get_overdue_invoices():
    settings = frappe.get_single("Collection Settings")
    min_amount = settings.minimum_overdue_amount or 0
    today = datetime.today().strftime("%Y-%m-%d")

    invoices = frappe.db.sql("""
        SELECT
            si.name as invoice,
            si.customer,
            si.customer_name,
            si.posting_date,
            si.due_date,
            si.grand_total,
            si.outstanding_amount,
            si.currency,
            DATEDIFF(%(today)s, si.due_date) as days_overdue,
            c.mobile_no,
            c.email_id as customer_email
        FROM `tabSales Invoice` si
        LEFT JOIN `tabCustomer` c ON c.name = si.customer
        WHERE
            si.docstatus = 1
            AND si.outstanding_amount > %(min_amount)s
            AND si.due_date < %(today)s
            AND si.company = %(company)s
        ORDER BY si.outstanding_amount DESC, days_overdue DESC
    """, {
        "today": today,
        "min_amount": min_amount,
        "company": frappe.defaults.get_user_default("Company")
    }, as_dict=True)

    for inv in invoices:
        inv["priority"] = get_priority(inv["days_overdue"])
        inv["last_reminder"] = get_last_reminder(inv["invoice"])

    return invoices


@frappe.whitelist(allow_guest=True)
def get_ar_summary():
    today = datetime.today().strftime("%Y-%m-%d")
    company = frappe.defaults.get_user_default("Company")

    result = frappe.db.sql("""
        SELECT
            COUNT(name) as total_invoices,
            SUM(outstanding_amount) as total_outstanding,
            SUM(CASE WHEN DATEDIFF(%(today)s, due_date) >= 30 THEN outstanding_amount ELSE 0 END) as critical_amount,
            SUM(CASE WHEN DATEDIFF(%(today)s, due_date) BETWEEN 15 AND 29 THEN outstanding_amount ELSE 0 END) as high_amount,
            SUM(CASE WHEN DATEDIFF(%(today)s, due_date) BETWEEN 7 AND 14 THEN outstanding_amount ELSE 0 END) as medium_amount
        FROM `tabSales Invoice`
        WHERE
            docstatus = 1
            AND outstanding_amount > 0
            AND due_date < %(today)s
            AND company = %(company)s
    """, {"today": today, "company": company}, as_dict=True)

    return result[0] if result else {}


def get_priority(days_overdue):
    if days_overdue >= 30:
        return "Critical"
    elif days_overdue >= 15:
        return "High"
    elif days_overdue >= 7:
        return "Medium"
    return "Low"


def get_last_reminder(invoice):
    return frappe.db.get_value(
        "Collection Log",
        {"sales_invoice": invoice},
        ["sent_on", "reminder_type", "status"],
        order_by="sent_on desc",
        as_dict=True
    ) or None


def load():
    pass
