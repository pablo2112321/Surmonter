# adminpanelApp/views.py
#from django.contrib.auth.decorators import login_required
from django.shortcuts import render

#@login_required
def paneladmin(request):
    return render(request, 'adminpanel/paneladmin.html')