from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def staff_console(request):
    display_name = request.user.get_full_name() or request.user.username or "เจ้าหน้าที่"
    return render(request, "staff_console.html", {"display_name": display_name})

@login_required
def equipment_view(request):
    return render(request, "placeholder.html", {"title": "ยืม-คืน อุปกรณ์กีฬา"})

@login_required
def badminton_booking_view(request):
    return render(request, "placeholder.html", {"title": "จองสนามแบดมินตัน"})

@login_required
def report_view(request):
    return render(request, "placeholder.html", {"title": "ข้อมูลการเข้าใช้สนาม"})

@login_required
def borrow_stats_view(request):
    return render(request, "placeholder.html", {"title": "ข้อมูลสถิติการยืม-คืน"})