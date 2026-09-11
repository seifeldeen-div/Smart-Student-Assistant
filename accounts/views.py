from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import RegisterForm
from .models import Profile

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            Profile.objects.create(user=user, role="student")
            login(request, user)
            return redirect("/")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})
