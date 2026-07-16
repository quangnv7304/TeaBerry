from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .models import LoyaltyAccount


@login_required
def loyalty_dashboard_view(
    request: HttpRequest,
) -> HttpResponse:
    account, _ = LoyaltyAccount.objects.get_or_create(
        customer=request.user,
    )
    transactions = (
        account.transactions
        .select_related("order")
        .order_by("-created_at")[:30]
    )
    tier_targets = {
        "MEMBER": 500,
        "SILVER": 1_500,
        "GOLD": 5_000,
        "PLATINUM": None,
    }
    next_tier_target = tier_targets.get(account.tier)
    points_to_next_tier = None
    if next_tier_target is not None:
        points_to_next_tier = max(
            0,
            next_tier_target - account.lifetime_points,
        )

    return render(
        request,
        "loyalty/dashboard.html",
        {
            "account": account,
            "transactions": transactions,
            "points_to_next_tier": points_to_next_tier,
        },
    )
