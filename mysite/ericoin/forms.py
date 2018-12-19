from django import forms


class TransactionForm(forms.Form):
    amount = forms.IntegerField(min_value=0, max_value=10**9)
    message = forms.CharField(max_length=1000, help_text="Personal message")
    recipient = forms.CharField(max_length=100, help_text="Public key of recipient")
    sender = forms.CharField(max_length=100, help_text="Public key of sender")
    signature = forms.CharField(max_length=100, help_text="Transaction signature")
    source = forms.CharField(max_length=50, widget=forms.HiddenInput())
    def clean(self):
        cleaned_data = super(TransactionForm, self).clean()
        amount = cleaned_data.get('amount')
        message = cleaned_data.get('message')
        recipient = cleaned_data.get('recipient')
        sender = cleaned_data.get('sender')
        signature = cleaned_data.get('signature')
        if not amount or not recipient or not sender or not signature:
            raise forms.ValidationError('Missing information!')

