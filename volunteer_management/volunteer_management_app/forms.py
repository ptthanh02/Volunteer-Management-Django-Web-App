from django import forms
from .models import *
from django.contrib.auth.forms import SetPasswordForm


class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['name', 'age', 'email', 'phone', 'address', 'skills']
        
class PasswordChangeForm(SetPasswordForm):
    old_password = forms.CharField(
        label="Mật khẩu cũ",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True}),
    )

    new_password1 = forms.CharField(
        label="Mật khẩu mới",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text="<ul><li>Mật khẩu của bạn không được giống với thông tin cá nhân quá đơn giản</li><li>Mật khẩu phải chứa ít nhất 8 ký tự</li><li>Mật khẩu không được hoàn toàn bằng số</li></ul>",
    )
    new_password2 = forms.CharField(
        label="Xác nhận mật khẩu mới",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    field_order = ['old_password', 'new_password1', 'new_password2']

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Mật khẩu cũ không đúng")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', "Mật khẩu mới không khớp")
        return cleaned_data