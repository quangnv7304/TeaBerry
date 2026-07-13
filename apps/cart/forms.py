from django import forms


class AddToCartForm(forms.Form):
    product_id = forms.IntegerField(
        min_value=1,
        widget=forms.HiddenInput(),
    )

    variant_id = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.HiddenInput(),
    )

    sugar_choice_id = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.HiddenInput(),
    )

    ice_choice_id = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.HiddenInput(),
    )

    toppings = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )

    quantity = forms.IntegerField(
        min_value=1,
        max_value=50,
        initial=1,
    )

    note = forms.CharField(
        required=False,
        max_length=255,
    )