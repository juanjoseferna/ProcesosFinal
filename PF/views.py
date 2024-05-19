from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponse
from .back import connect_to_mongo, deliver_data, obtener_clima , get_all_devices, get_order_history
import datetime
from datetime import date, timedelta
user = None

def Login(request):
    global user
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        # Conectar a MongoDB y guardar los datos
        flag = connect_to_mongo(username, password)
        print(flag)
        if not flag:
            return render(request, 'Login.html', {'messages': 'Incorrect username or password'})
        else:
            user = username
            return redirect('menu')
    else:
        return render(request, 'Login.html')

def menu(request):
    return render(request, 'menu.html', {'user': user})

def header(request):
    return render(request, 'header.html')

def weather(request):
    clima = obtener_clima()
    return render(request, 'weather.html', {'clima': clima})

def deliver(request):
    
    if request.method == 'POST':
        dispositivo = request.POST['dispositivo']
        fecha = request.POST['date']
        hora = request.POST['time']
        hora = datetime.datetime.strptime(hora, '%H:%M').strftime('%I:%M %p')
        destino = request.POST['destination']
        producto = request.POST['product']
        peso = request.POST['weight']
        name1 = request.POST['emit']
        name2 = request.POST['receive']
        phone1 = request.POST['phone1']
        phone2 = request.POST['phone2']
        email1 = request.POST['email1']
        email2 = request.POST['email2']
        # print(fecha, hora, destino, producto, peso) -- 2024-05-16 09:41 PM Palmas Coca-cola 50
        flag, mensaje = deliver_data(dispositivo, fecha, hora, destino, producto, peso, name1, name2, phone1, phone2, email1, email2)
        return render(request, 'deliver.html', {'messages': mensaje, 'flag': flag})
    return render(request, 'deliver.html')

def devices(request):
    drones, robots = get_all_devices()
    # Convertir ObjectId a string y cambiar la clave '_id' a 'id'
    for drone in drones:
        drone['id'] = str(drone.pop('_id'))
    for robot in robots:
        robot['id'] = str(robot.pop('_id'))
    return render(request, 'Devices.html', {'drones': drones, 'robots': robots})

def history(request):
    orders = get_order_history()
    return render(request, 'history.html', {'orders': orders})

def dateD(request):
    today = date.today()
    limit = today + timedelta(days=7)
    context = {
        'today': today.strftime('%Y-%m-%d'),
        'limit': limit.strftime('%Y-%m-%d'),
    }
    return render(request, 'deliver.html', context)