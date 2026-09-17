from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import redirect, render
from .forms import UserRegisterForm

# Create your views here.
def register_view(request):
    if request.user.is_authenticated:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('accounts:login')
    else:
        form = UserRegisterForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            if user.is_blocked:
                messages.error(request, "আপনার একাউন্টটি সাময়িকভাবে ব্লক করা হয়েছে।")
                return redirect('accounts:login')
                
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('custom_admin:dashboard')
            return redirect('/')
        else:
            messages.error(request, "ইউজারনেম বা পাসওয়ার্ড ভুল হয়েছে।")

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "আপনি সফলভাবে লগআউট করেছেন।")
    return redirect('accounts:login')