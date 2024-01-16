from django import forms


class RequestForm(forms.Form):
    comment = forms.CharField(
        label="",
        widget=forms.Textarea,
        required=False
    )