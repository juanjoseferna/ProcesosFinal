from django.contrib import admin
from django.urls import path
from PF.views import Login, menu, weather, header, deliver, devices, history

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', Login, name='login'),
    path('home/', menu, name='menu'),
    path('weather/', weather, name='weather'),
    path('header/', header, name='header'),
    path('deliver/', deliver, name='deliver'),
    path('devices/', devices, name='devices'), 
    path('history/', history, name='history')
]
