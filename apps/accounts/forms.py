from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

from .models import Address, User


class TeaBerryPasswordChangeForm(PasswordChangeForm):
    """Password change form styled consistently with the storefront."""

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)

        field_options = {
            "old_password": (
                "Mật khẩu hiện tại",
                "current-password",
            ),
            "new_password1": (
                "Mật khẩu mới",
                "new-password",
            ),
            "new_password2": (
                "Nhập lại mật khẩu mới",
                "new-password",
            ),
        }

        for name, (label, autocomplete) in field_options.items():
            field = self.fields[name]
            field.label = label
            field.widget.attrs.update(
                {
                    "class": "form-control",
                    "autocomplete": autocomplete,
                }
            )


class TeaBerryPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "email@example.com",
                "autocomplete": "email",
                "autofocus": True,
            }
        ),
    )


class TeaBerrySetPasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        labels = {
            "new_password1": "Mật khẩu mới",
            "new_password2": "Nhập lại mật khẩu mới",
        }
        for name, label in labels.items():
            self.fields[name].label = label
            self.fields[name].widget.attrs.update(
                {
                    "class": "form-control",
                    "autocomplete": "new-password",
                }
            )


class TeaBerryLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "staff@teaberry.local",
                "autocomplete": "email",
                "autofocus": True,
            }
        ),
    )

    password = forms.CharField(
        label="Mật khẩu",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập mật khẩu",
                "autocomplete": "current-password",
            }
        ),
    )

class CustomerRegisterForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=150,
        label="Họ và tên",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nguyễn Văn A",
                "autocomplete": "name",
            }
        ),
    )

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "email@example.com",
                "autocomplete": "email",
            }
        ),
    )

    phone = forms.CharField(
        max_length=20,
        label="Số điện thoại",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "0901234567",
                "autocomplete": "tel",
            }
        ),
    )

    password1 = forms.CharField(
        label="Mật khẩu",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
    )

    password2 = forms.CharField(
        label="Nhập lại mật khẩu",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "full_name",
            "email",
            "phone",
            "password1",
            "password2",
        )

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Email này đã được sử dụng."
            )

        return email

    def clean_phone(self) -> str:
        phone = (
            self.cleaned_data["phone"]
            .replace(" ", "")
            .replace(".", "")
            .replace("-", "")
        )

        if not phone.isdigit():
            raise forms.ValidationError(
                "Số điện thoại chỉ được chứa chữ số."
            )

        if len(phone) < 9 or len(phone) > 15:
            raise forms.ValidationError(
                "Số điện thoại không hợp lệ."
            )

        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                "Số điện thoại này đã được sử dụng."
            )

        return phone
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = (
            "recipient_name",
            "recipient_phone",
            "address_line",
            "ward",
            "district",
            "province",
            "label",
            "delivery_note",
            "is_default",
        )

        widgets = {
            "recipient_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "name",
                }
            ),
            "recipient_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "tel",
                }
            ),
            "address_line": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Số nhà, tên đường...",
                }
            ),
            "ward": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "district": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "province": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "label": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nhà, Công ty...",
                }
            ),
            "delivery_note": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Gọi trước khi giao...",
                }
            ),
            "is_default": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def clean_recipient_phone(self) -> str:
        phone = (
            self.cleaned_data["recipient_phone"]
            .replace(" ", "")
            .replace(".", "")
            .replace("-", "")
        )

        if not phone.isdigit():
            raise forms.ValidationError(
                "Số điện thoại chỉ được chứa chữ số."
            )

        if len(phone) < 9 or len(phone) > 15:
            raise forms.ValidationError(
                "Số điện thoại không hợp lệ."
            )

        return phone
