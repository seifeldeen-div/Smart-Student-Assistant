from django.db import transaction
from django.shortcuts import render, redirect
from .forms import RegisterForm
from .models import Profile


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                role = form.cleaned_data["role"]
                user.is_active = role == "student"
                user.save(update_fields=["is_active"])
                Profile.objects.create(
                    user=user,
                    role=role,
                    cv_file=form.cleaned_data.get("cv_file"),
                )
            if role == "instructor":
                return render(request, "accounts/pending_approval.html")
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})
