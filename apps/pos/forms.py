from django import forms

from apps.orders.models import FulfillmentType


class PosCheckoutForm(forms.Form):
    fulfillment_type = forms.ChoiceField(
        choices=(
            (
                FulfillmentType.PICKUP,
                "Khách mang về",
            ),
            (
                FulfillmentType.DINE_IN,
                "Dùng tại quán",
            ),
        ),
        label="Hình thức nhận món",
        widget=forms.RadioSelect(),
    )

    customer_name = forms.CharField(
        max_length=150,
        required=False,
        label="Tên khách hàng",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Khách lẻ",
            }
        ),
    )

    customer_phone = forms.CharField(
        max_length=20,
        required=False,
        label="Số điện thoại",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Không bắt buộc",
            }
        ),
    )

    table_number = forms.CharField(
        max_length=20,
        required=False,
        label="Số bàn",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ví dụ: B05",
            }
        ),
    )

    note = forms.CharField(
        max_length=255,
        required=False,
        label="Ghi chú",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Ghi chú cho đơn tại quầy",
            }
        ),
    )

    def clean_customer_phone(self) -> str:
        phone = self.cleaned_data.get(
            "customer_phone",
            "",
        )

        normalized = (
            phone.replace(" ", "")
            .replace(".", "")
            .replace("-", "")
        )

        if normalized and not normalized.isdigit():
            raise forms.ValidationError(
                "Số điện thoại chỉ được chứa chữ số."
            )

        return normalized

    def clean(self):
        cleaned_data = super().clean()

        fulfillment_type = cleaned_data.get(
            "fulfillment_type"
        )

        table_number = cleaned_data.get(
            "table_number",
            "",
        ).strip()

        if (
            fulfillment_type
            == FulfillmentType.DINE_IN
            and not table_number
        ):
            self.add_error(
                "table_number",
                "Vui lòng nhập số bàn.",
            )

        return cleaned_data