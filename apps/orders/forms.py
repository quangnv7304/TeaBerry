from django import forms

from .models import PaymentMethod


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(
        max_length=150,
        label="Họ và tên người nhận",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nguyễn Văn A",
                "autocomplete": "name",
            }
        ),
    )

    customer_phone = forms.CharField(
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

    customer_email = forms.EmailField(
        required=False,
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "email@example.com",
                "autocomplete": "email",
            }
        ),
    )

    shipping_address = forms.CharField(
        max_length=500,
        label="Địa chỉ giao hàng",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": (
                    "Số nhà, đường, phường/xã, quận/huyện..."
                ),
                "autocomplete": "street-address",
            }
        ),
    )

    delivery_note = forms.CharField(
        required=False,
        max_length=500,
        label="Ghi chú giao hàng",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": (
                    "Ví dụ: Gọi điện trước khi giao..."
                ),
            }
        ),
    )

    voucher_code = forms.CharField(
        required=False,
        max_length=50,
        label="Mã giảm giá",
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-uppercase",
                "placeholder": "Ví dụ: WELCOME20",
                "autocomplete": "off",
            }
        ),
    )

    loyalty_points = forms.IntegerField(
        required=False,
        min_value=0,
        initial=0,
        label="Điểm thưởng muốn đổi",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "100",
                "placeholder": "Ví dụ: 100",
            }
        ),
    )

    payment_method = forms.ChoiceField(
        choices=PaymentMethod.choices,
        initial=PaymentMethod.COD,
        label="Phương thức thanh toán",
        widget=forms.RadioSelect(),
    )

    def clean_customer_phone(self) -> str:
        phone = self.cleaned_data["customer_phone"]

        normalized_phone = (
            phone.replace(" ", "")
            .replace(".", "")
            .replace("-", "")
        )

        if not normalized_phone.isdigit():
            raise forms.ValidationError(
                "Số điện thoại chỉ được chứa chữ số."
            )

        if len(normalized_phone) < 9 or len(normalized_phone) > 15:
            raise forms.ValidationError(
                "Số điện thoại không hợp lệ."
            )

        return normalized_phone
