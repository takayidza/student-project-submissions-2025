from django.shortcuts import render

def Reports(request):
    return render(request, "Reports/Reports.html")
