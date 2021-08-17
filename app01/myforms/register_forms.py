# 书写针对用户表的forms组件代码
from django import forms

from app01 import models


class MyRegForm(forms.Form):
    username = forms.CharField(label='用户名', min_length=8, max_length=24,
                               error_messages={
                                   'required': '用户名不能为空',
                                   'min_length': "用户名最少8位",
                                   'max_length': "用户名最大24位"
                               },
                               # 还需要让标签有bootstrap样式
                               widget=forms.widgets.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名，长度为8-24位，建议使用手机号作为用户名'}))

    password = forms.CharField(label='密码', min_length=8, max_length=24,
                               error_messages={
                                   'required': '密码不能为空',
                                   'min_length': "密码最少8位",
                                   'max_length': "密码最大24位"
                               },
                               # 还需要让标签有bootstrap样式
                               widget=forms.widgets.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请设置你的密码，长度为8-24位'}))

    confirm_password = forms.CharField(label='确认密码', min_length=8, max_length=24,
                                       error_messages={
                                           'required': '确认密码不能为空',
                                           'min_length': "确认密码最少8位",
                                           'max_length': "确认密码最大24位",
                                       },
                                       # 还需要让标签有bootstrap样式
                                       widget=forms.widgets.PasswordInput(attrs={'class': 'form-control', 'placeholder': '再次输入密码'}))
    email = forms.EmailField(label='邮箱',
                             error_messages={
                                 'required': '邮箱不能为空',
                                 'invalid': '邮箱格式不正确'
                             },
                             widget=forms.widgets.EmailInput(attrs={'class': 'form-control', 'placeholder': '请输入你常用的邮箱'}))

    # 钩子函数
    # 局部钩子:校验用户名是否已存在
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # 去数据库中校验
        is_exist = models.UserInfo.objects.filter(username=username)
        if is_exist:
            # 提示信息
            self.add_error('username', '用户名已被注册')
        return username

    # 全局钩子:校验两次是否一致
    def clean(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if not password == confirm_password:
            self.add_error('confirm_password', '两次密码不一致')
        return self.cleaned_data
