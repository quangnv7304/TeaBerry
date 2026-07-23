from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from apps.accounts.models import UserRole

from .forms import (
    AddressForm,
    CustomerRegisterForm,
    TeaBerryLoginForm,
    TeaBerryPasswordChangeForm,
    TeaBerryPasswordResetForm,
    TeaBerrySetPasswordForm,
)
from .models import Address
from .services import save_address, set_default_address


@login_required
def loyalty_view(request):
    from apps.loyalty.models import LoyaltyAccount

    account, _ = LoyaltyAccount.objects.get_or_create(
        customer=request.user,
    )
    transactions = account.transactions.select_related("order")[:10]
    return render(
        request,
        "accounts/loyalty.html",
        {"account": account, "transactions": transactions},
    )

class TeaBerryLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = TeaBerryLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        next_url = self.get_redirect_url()

        if next_url:
            return next_url

        user = self.request.user

        if user.is_superuser:
            return reverse_lazy("dashboard:home")

        if user.role in {
            UserRole.STAFF,
            UserRole.MANAGER,
            UserRole.ADMIN,
        }:
            return reverse_lazy("dashboard:home")

        return reverse_lazy("catalog:product-list")


@login_required
@require_http_methods(["GET", "POST"])
def password_change_view(request):
    form = TeaBerryPasswordChangeForm(
        user=request.user,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Đổi mật khẩu thành công.")
        return redirect("accounts:password-change")

    return render(
        request,
        "accounts/password_change.html",
        {"form": form},
    )


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("catalog:product-list")

    if request.method == "POST":
        form = CustomerRegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.phone = form.cleaned_data["phone"]
            user.full_name = form.cleaned_data["full_name"]
            user.role = UserRole.CUSTOMER
            user.is_staff = False
            user.is_superuser = False
            user.save()

            login(request, user)

            messages.success(
                request,
                "Tạo tài khoản thành công.",
            )

            return redirect("catalog:product-list")
    else:
        form = CustomerRegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )
@login_required
def address_list_view(request):
    addresses = (
        Address.objects
        .filter(
            user=request.user,
            is_active=True,
        )
        .order_by(
            "-is_default",
            "-updated_at",
        )
    )

    return render(
        request,
        "accounts/address_list.html",
        {
            "addresses": addresses,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def address_create_view(request):
    if request.method == "POST":
        form = AddressForm(request.POST)

        if form.is_valid():
            save_address(
                user=request.user,
                form=form,
            )

            messages.success(
                request,
                "Đã thêm địa chỉ mới.",
            )

            return redirect(
                "accounts:address-list"
            )
    else:
        form = AddressForm(
            initial={
                "recipient_name": request.user.full_name,
                "recipient_phone": request.user.phone or "",
            }
        )

    return render(
        request,
        "accounts/address_form.html",
        {
            "form": form,
            "page_title": "Thêm địa chỉ",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def address_update_view(
    request,
    address_id,
):
    address = get_object_or_404(
        Address,
        pk=address_id,
        user=request.user,
        is_active=True,
    )

    if request.method == "POST":
        form = AddressForm(
            request.POST,
            instance=address,
        )

        if form.is_valid():
            save_address(
                user=request.user,
                form=form,
                address=address,
            )

            messages.success(
                request,
                "Đã cập nhật địa chỉ.",
            )

            return redirect(
                "accounts:address-list"
            )
    else:
        form = AddressForm(
            instance=address,
        )

    return render(
        request,
        "accounts/address_form.html",
        {
            "form": form,
            "page_title": "Sửa địa chỉ",
        },
    )


@login_required
@require_http_methods(["POST"])
def address_set_default_view(
    request,
    address_id,
):
    address = get_object_or_404(
        Address,
        pk=address_id,
        user=request.user,
        is_active=True,
    )

    set_default_address(
        user=request.user,
        address=address,
    )

    messages.success(
        request,
        "Đã đặt làm địa chỉ mặc định.",
    )

    return redirect("accounts:address-list")


@login_required
@require_http_methods(["POST"])
def address_delete_view(
    request,
    address_id,
):
    address = get_object_or_404(
        Address,
        pk=address_id,
        user=request.user,
        is_active=True,
    )

    was_default = address.is_default

    address.is_active = False
    address.is_default = False
    address.save(
        update_fields=[
            "is_active",
            "is_default",
            "updated_at",
        ]
    )

    if was_default:
        next_address = (
            Address.objects
            .filter(
                user=request.user,
                is_active=True,
            )
            .order_by("-updated_at")
            .first()
        )

        if next_address:
            set_default_address(
                user=request.user,
                address=next_address,
            )

    messages.success(
        request,
        "Đã xóa địa chỉ.",
    )

    return redirect("accounts:address-list")

class TeaBerryLogoutView(LogoutView):
    next_page = reverse_lazy("catalog:product-list")


class TeaBerryPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    form_class = TeaBerryPasswordResetForm
    success_url = reverse_lazy("accounts:password-reset-done")


class TeaBerryPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class TeaBerryPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = TeaBerrySetPasswordForm
    success_url = reverse_lazy("accounts:password-reset-complete")


class TeaBerryPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
