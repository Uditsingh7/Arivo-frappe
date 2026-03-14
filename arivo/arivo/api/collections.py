import frappe
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def get_overdue_invoices():
    settings = frappe.get_single("Collection Settings")
    min_amount = settings.minimum_overdue_amount or 0
    today = datetime.today().strftime("%Y-%m-%d")

    invoices = frappe.db.sql(
        """
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
        """,
        {"today": today, "min_amount": min_amount},
        as_dict=True,
    )

    invoice_names = [inv["invoice"] for inv in invoices]
    last_log_map = {}

    if invoice_names:
        logs = frappe.db.sql(
            """
            SELECT
                sales_invoice as invoice,
                email_subject as subject,
                status,
                creation,
                COUNT(*) OVER (PARTITION BY sales_invoice) as reminder_count
            FROM `tabCollection Log`
            WHERE sales_invoice IN %(names)s
            ORDER BY creation DESC
            """,
            {"names": tuple(invoice_names)},
            as_dict=True,
        )
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
    result = frappe.db.sql(
        """
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
        """,
        {"today": today},
        as_dict=True,
    )
    return result[0] if result else {}


@frappe.whitelist(allow_guest=True)
def get_daily_briefing():
    today = datetime.today().strftime("%Y-%m-%d")
    yesterday = (
        datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        .fromordinal(datetime.today().toordinal() - 1)
        .strftime("%Y-%m-%d")
    )

    broken = frappe.db.sql(
        """
        SELECT
            COUNT(DISTINCT apl.parent) as invoice_count,
            COALESCE(SUM(si.outstanding_amount), 0) as total_amount
        FROM `tabAR Promise Log` apl
        JOIN `tabSales Invoice` si ON si.name = apl.parent
        WHERE
            apl.parenttype = 'Sales Invoice'
            AND apl.promise_status = 'Broken'
            AND si.docstatus = 1
            AND si.outstanding_amount > 0
        """,
        as_dict=True,
    )[0]

    no_contact = frappe.db.sql(
        """
        SELECT
            COUNT(*) as invoice_count,
            COALESCE(SUM(si.outstanding_amount), 0) as total_amount
        FROM `tabSales Invoice` si
        LEFT JOIN (
            SELECT sales_invoice, MAX(creation) as last_touch
            FROM `tabCollection Log`
            GROUP BY sales_invoice
        ) cl ON cl.sales_invoice = si.name
        WHERE
            si.docstatus = 1
            AND si.outstanding_amount > 0
            AND si.due_date < %(today)s
            AND (cl.last_touch IS NULL OR DATEDIFF(%(today)s, cl.last_touch) > 10)
        """,
        {"today": today},
        as_dict=True,
    )[0]

    newly_30 = frappe.db.sql(
        """
        SELECT
            COUNT(*) as invoice_count,
            COALESCE(SUM(outstanding_amount), 0) as total_amount
        FROM `tabSales Invoice`
        WHERE
            docstatus = 1
            AND outstanding_amount > 0
            AND due_date < %(today)s
            AND DATEDIFF(%(today)s, due_date) >= 30
            AND DATEDIFF(%(yesterday)s, due_date) < 30
        """,
        {"today": today, "yesterday": yesterday},
        as_dict=True,
    )[0]

    return {
        "broken_promises": {
            "count": int(broken["invoice_count"] or 0),
            "amount": float(broken["total_amount"] or 0),
        },
        "no_contact_gt_10d": {
            "count": int(no_contact["invoice_count"] or 0),
            "amount": float(no_contact["total_amount"] or 0),
        },
        "newly_30_plus": {
            "count": int(newly_30["invoice_count"] or 0),
            "amount": float(newly_30["total_amount"] or 0),
        },
    }


@frappe.whitelist(allow_guest=True)
def get_overdue_invoices_paged(page=1, page_size=50, attention_type="all"):
    settings = frappe.get_single("Collection Settings")
    min_amount = settings.minimum_overdue_amount or 0
    today = datetime.today().strftime("%Y-%m-%d")

    try:
        page = max(1, int(page))
        page_size = min(200, max(1, int(page_size)))
    except Exception:
        page, page_size = 1, 50

    offset = (page - 1) * page_size

    attention_join = ""
    attention_where = ""

    if attention_type == "broken_promises":
        attention_join = """
            JOIN `tabAR Promise Log` apl_f
                ON apl_f.parent = si.name
                AND apl_f.parenttype = 'Sales Invoice'
                AND apl_f.promise_status = 'Broken'
        """
    elif attention_type == "no_contact_gt_10d":
        attention_join = """
            LEFT JOIN (
                SELECT sales_invoice, MAX(creation) as last_touch
                FROM `tabCollection Log`
                GROUP BY sales_invoice
            ) cl_f ON cl_f.sales_invoice = si.name
        """
        attention_where = """
            AND (cl_f.last_touch IS NULL OR DATEDIFF(%(today)s, cl_f.last_touch) > 10)
        """
    elif attention_type == "newly_30_plus":
        attention_where = """
            AND DATEDIFF(%(today)s, si.due_date) >= 30
            AND DATEDIFF(DATE_SUB(%(today)s, INTERVAL 1 DAY), si.due_date) < 30
        """
    elif attention_type == "never_contacted":
        attention_join = """
            LEFT JOIN `tabCollection Log` cl_nc ON cl_nc.sales_invoice = si.name
        """
        attention_where = "AND cl_nc.sales_invoice IS NULL"

    params = {"today": today, "min_amount": min_amount, "page_size": page_size, "offset": offset}

    count_result = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT si.name) as total
        FROM `tabSales Invoice` si
        {attention_join}
        WHERE si.docstatus = 1
          AND si.outstanding_amount > %(min_amount)s
          AND si.due_date < %(today)s
          {attention_where}
    """, params, as_dict=True)

    total_count = count_result[0]["total"] if count_result else 0

    invoices = frappe.db.sql(f"""
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
        {attention_join}
        WHERE si.docstatus = 1
          AND si.outstanding_amount > %(min_amount)s
          AND si.due_date < %(today)s
          {attention_where}
        GROUP BY si.name
        ORDER BY si.outstanding_amount DESC, days_overdue DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, params, as_dict=True)

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
        """, {"names": tuple(invoice_names)}, as_dict=True)

        for log in logs:
            if log["invoice"] not in last_log_map:
                last_log_map[log["invoice"]] = log

    for inv in invoices:
        inv["priority"] = get_priority(inv["days_overdue"])
        inv["last_action"] = last_log_map.get(inv["invoice"])
        inv["reminder_count"] = last_log_map.get(inv["invoice"], {}).get("reminder_count", 0)

    return {
        "invoices": invoices,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
    }


def get_priority(days_overdue: int) -> str:
    if days_overdue >= 30:
        return "Critical"
    elif days_overdue >= 15:
        return "High"
    elif days_overdue >= 7:
        return "Medium"
    return "Low"


def load():
    pass
