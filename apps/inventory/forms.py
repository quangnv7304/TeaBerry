from django import forms


class ImportStockForm(forms.Form):
    quantity = forms.DecimalField(
        min_value=0.01,
        max_digits=12,
        decimal_places=2,
        label="Số lượng nhập",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "placeholder": "Nhập số lượng",
            }
        ),
    )

    note = forms.CharField(
        required=False,
        max_length=255,
        label="Ghi chú",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ví dụ: Nhập hàng ngày 15/07",
            }
        ),
    )