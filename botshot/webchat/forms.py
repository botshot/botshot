from django import forms


class MessageForm(forms.Form):
    message = forms.CharField(
        label='Message',
        max_length=1024,
        widget=forms.TextInput(attrs={'placeholder': 'Type message here'})
    )
