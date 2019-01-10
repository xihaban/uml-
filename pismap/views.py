from django.shortcuts import render
from django.contrib.auth import authenticate,login
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib import auth
from django import forms
from django.contrib.auth.models import User


def login(request):
    return render(request,"login.html")

def panel(request):
    return  render(request,"panel.html")


class UserForm(forms.Form):
    username = forms.CharField(label='用户名', max_length=100)
    password = forms.CharField(label='密码', widget=forms.PasswordInput())

def index(request):
    return render(request, 'index.html')


def regist(request):
    if request.method == 'POST':
        uf = UserForm(request.POST)
        if uf.is_valid():
            username = uf.cleaned_data['username']
            password = uf.cleaned_data['password']
            registAdd = User.objects.create_user(username=username, password=password)
            if registAdd == False:
                return render(request, 'share1.html', {'registAdd': registAdd, 'username': username})

            else:
                return render(request, 'share1.html', {'registAdd': registAdd})
    else:
        uf = UserForm()
    return render(request, 'regist1.html', {'uf': uf})


def login1(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        re = auth.authenticate(username=username, password=password)
        if re is not None:
            auth.login(request, re)
            return redirect('/', {'user': re})
        else:
            return render(request, 'login1.html', {'login_error': '用户名或密码错误'})
    return render(request, 'login1.html')


def logout(request):
    auth.logout(request)
    return render(request, 'index.html')



