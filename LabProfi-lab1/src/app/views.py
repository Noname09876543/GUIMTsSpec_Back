from django.shortcuts import render
from app import data


def home_page(request):
    return render(request, "home.html")

def services_list_page(request):
    query = request.GET.get("q")
    if query:
        specialists = [s for s in data.specialists if query.lower() in s['name'].lower()]
    else:
        specialists = data.specialists
    return render(request, "service_select.html", {"specialists": specialists, "query": query})

def service_page(request, id):
    return render(request, "service_info.html", {"specialist": data.specialists[id]})