from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .permissions import ensure_report_access
from .services import (
    get_daily_revenue,
    get_report_date_range,
    get_report_summary,
    get_top_products,
)


@login_required
def revenue_dashboard_view(
    request: HttpRequest,
) -> HttpResponse:
    ensure_report_access(request.user)

    try:
        days = int(
            request.GET.get("days", 7)
        )
    except (TypeError, ValueError):
        days = 7

    if days not in {7, 30, 90}:
        days = 7

    start_date, end_date = (
        get_report_date_range(
            days=days,
        )
    )

    summary = get_report_summary(
        start_date=start_date,
        end_date=end_date,
    )

    daily_revenue = get_daily_revenue(
        start_date=start_date,
        end_date=end_date,
    )

    top_products = get_top_products(
        start_date=start_date,
        end_date=end_date,
    )

    return render(
        request,
        "reports/revenue_dashboard.html",
        {
            "days": days,
            "start_date": start_date,
            "end_date": end_date,
            "summary": summary,
            "daily_revenue": daily_revenue,
            "top_products": top_products,
            "chart_labels": [
                row["date_label"]
                for row in daily_revenue
            ],
            "chart_values": [
                row["revenue"]
                for row in daily_revenue
            ],
        },
    )