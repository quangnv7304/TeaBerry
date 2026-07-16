from django import forms


class OpenShiftForm(forms.Form):
    store_id = forms.IntegerField(
        min_value=1,
        widget=forms.HiddenInput(),
    )

    opening_cash = forms.IntegerField(
        min_value=0,
        initial=0,
        label="Tiền mặt đầu ca",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "1000",
            }
        ),
    )

    opening_note = forms.CharField(
        required=False,
        max_length=255,
        label="Ghi chú",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ví dụ: Nhận bàn giao từ ca sáng",
            }
        ),
    )


class CloseShiftForm(forms.Form):
    actual_cash = forms.IntegerField(
        min_value=0,
        label="Tiền mặt kiểm đếm thực tế",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "1000",
            }
        ),
    )

    closing_note = forms.CharField(
        required=False,
        max_length=255,
        label="Ghi chú đóng ca",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
            }
        ),
    )