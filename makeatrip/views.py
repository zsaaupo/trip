"""
Server-rendered page views. These mostly just return the HTML shell;
the actual data is loaded client-side via JS calls to the REST API
(see static/js/). A handful of pages pass small bits of context
(e.g. an id from the URL, or whether the visitor is logged in/admin).
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect


def home(request):
    return render(request, 'home.html')


# --------------------------------------------------------------------- #
# Accounts
# --------------------------------------------------------------------- #
def register_page(request):
    if request.user.is_authenticated:
        return redirect('page-dashboard')
    return render(request, 'accounts/register.html')


def verify_otp_page(request):
    return render(request, 'accounts/verify_otp.html', {'email': request.GET.get('email', '')})


def login_page(request):
    if request.user.is_authenticated:
        return redirect('page-dashboard')
    return render(request, 'accounts/login.html')


def forgot_password_page(request):
    return render(request, 'accounts/forgot_password.html')


def reset_password_page(request):
    return render(request, 'accounts/reset_password.html', {'email': request.GET.get('email', '')})


@login_required(login_url='page-login')
def profile_page(request):
    return render(request, 'accounts/profile.html')


# --------------------------------------------------------------------- #
# Dashboards
# --------------------------------------------------------------------- #
@login_required(login_url='page-login')
def dashboard_page(request):
    if request.user.is_staff:
        return redirect('page-admin-dashboard')
    return render(request, 'dashboard/customer_dashboard.html')


@user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='page-login')
def admin_dashboard_page(request):
    return render(request, 'dashboard/admin_dashboard.html')


# --------------------------------------------------------------------- #
# Hotels
# --------------------------------------------------------------------- #
def hotel_list_page(request):
    return render(request, 'hotels/list.html')


def hotel_detail_page(request, pk):
    return render(request, 'hotels/detail.html', {'hotel_id': pk})


# --------------------------------------------------------------------- #
# Transportation
# --------------------------------------------------------------------- #
def transport_choose_page(request):
    return render(request, 'transportation/choose.html')


def bus_list_page(request):
    return render(request, 'transportation/bus_list.html')


def bus_detail_page(request, pk):
    return render(request, 'transportation/bus_detail.html', {'bus_id': pk})


def car_list_page(request):
    return render(request, 'transportation/car_list.html')


def car_detail_page(request, pk):
    return render(request, 'transportation/car_detail.html', {'car_id': pk})


# --------------------------------------------------------------------- #
# Packages
# --------------------------------------------------------------------- #
def package_list_page(request):
    return render(request, 'packages/list.html')


def package_detail_page(request, pk):
    return render(request, 'packages/detail.html', {'package_id': pk})


# --------------------------------------------------------------------- #
# Booking history
# --------------------------------------------------------------------- #
@login_required(login_url='page-login')
def booking_history_page(request):
    return render(request, 'bookings/history.html')
