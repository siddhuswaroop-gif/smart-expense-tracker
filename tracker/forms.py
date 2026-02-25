from django import forms
from .models import Transaction, Category

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'type', 'category', 'date', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        
        self.fields['category'].queryset = Category.objects.all()

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero")
        return amount