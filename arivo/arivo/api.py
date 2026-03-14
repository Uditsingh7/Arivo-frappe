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
            si.company,
            DATEDIFF(%(today)s, si.due_date) as days_overdue,
            c.mobile_no,
            c.email_id as customer_email
        FROM `tabSales Invoice` si
        LEFT JOIN `tabCustomer` c ON c.name = si.customer
        WHERE
            si.docstatus = 1
            AND si.outstanding_amount > %(min_amount)s
            AND si.due_date < %(today)s
        ORDER BY si.outstanding_amount DESC, days_overdue DESC
    """, {
        "today": today,
        "min_amount": min_amount,
    }, as_dict=True)

    invoice_names = [inv["invoice"] for inv in invoices]
    last_log_map = {}

    if invoice_names:
        logs = frappe.db.sql("""
            SELECT
                sales_invoice as invoice,
                email_subject as subject,
                status,
                creation,
                COUNT(*) OVER (PARTITION BY sales_invoice) as reminder_count
            FROM `tabCollection Log`
            WHERE sales_invoice IN %(names)s
            ORDER BY creation DESC
        """, {"names": invoice_names}, as_dict=True)

        for log in logs:
            if log["invoice"] not in last_log_map:
                last_log_map[log["invoice"]] = log

    for inv in invoices:
        inv["priority"] = get_priority(inv["days_overdue"])
        inv["last_action"] = last_log_map.get(inv["invoice"])
        inv["reminder_count"] = last_log_map.get(inv["invoice"], {}).get("reminder_count", 0)

    return invoices


@frappe.whitelist(allow_guest=True)
def get_ar_summary():
    today = datetime.today().strftime("%Y-%m-%d")

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
    """, {"today": today}, as_dict=True)

    return result[0] if result else {}


def get_priority(days_overdue):
    if days_overdue >= 30:
        return "Critical"
    elif days_overdue >= 15:
        return "High"
    elif days_overdue >= 7:
        return "Medium"
    return "Low"


def load():
    pass
