from django.shortcuts import render
from django.conf import settings

def page_not_found_view(request, exception):
    return render(request, '404.html', {'site_url': settings.SITE_URL}, status=404)