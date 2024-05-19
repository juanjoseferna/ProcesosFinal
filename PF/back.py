from pymongo.mongo_client import MongoClient
import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

uri = "" #TODO "mongodb+srv://<username>:<password>@<cluster>/<database>?retryWrites=true&w=majority
client = MongoClient(uri)

def enviar_correo(destinatario, asunto, cuerpo):
    remitente = '' #TODO email
    contrasena = '' #TODO password

    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto

    mensaje.attach(MIMEText(cuerpo, 'plain'))

    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(remitente, contrasena)
        texto = mensaje.as_string()
        servidor.sendmail(remitente, destinatario, texto)
        servidor.quit()
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False

def obtener_descripcion_clima(weathercode):
    weather_descriptions = {
        0: "Clear",
        1: "Mostly clear",
        2: "Partly cloudy",
        3: "Cloudy",
        45: "Fog",
        48: "Freezing fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Heavy drizzle",
        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Light showers",
        81: "Moderate showers",
        82: "Heavy showers"
        # Añadir más códigos según sea necesario
    }
    return weather_descriptions.get(weathercode, "Desconocido")

def obtener_clima():
    latitud = 3.4516
    longitud = -76.5320
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitud}&longitude={longitud}&current_weather=true&timezone=America/Bogota"
    
    try:
        respuesta = requests.get(url)
        respuesta.raise_for_status()  # Esto lanzará una excepción si el código de estado no es 200
        datos = respuesta.json()
        clima_actual = datos.get("current_weather")

        if clima_actual:
            descripcion_clima = obtener_descripcion_clima(clima_actual["weathercode"])
            condiciones_no_aptas = [51, 53, 55, 61, 63, 65, 71, 73, 75, 80, 81, 82]
            clima_apto = True

            if clima_actual["windspeed"] > 32 or clima_actual["weathercode"] in condiciones_no_aptas:
                clima_apto = False

            return {
                "temperatura": clima_actual["temperature"],
                "viento": clima_actual["windspeed"],
                "direccion_viento": clima_actual["winddirection"],
                "tiempo": descripcion_clima,
                "clima_apto": clima_apto
            }
        else:
            print("No se pudo obtener 'current_weather' en la respuesta.")
            return None

    except requests.RequestException as e:
        print(f"Error al hacer la solicitud: {e}")
        return None

def connect_to_mongo(username, password):

    db = client.get_database('ProcesosFinal')

    # Verificar si el usuario ya existe en la colección "users"
    users_collection = db.get_collection('users')
    existing_user = users_collection.find_one({"user": username})
    
    if existing_user != None and existing_user['password'] == password:
        return True
    return False

def deliver_data(dispositivo, fecha, hora, destino, producto, peso, name1, name2, phone1, phone2, email1, email2):
    db = client.get_database('ProcesosFinal')
    if dispositivo == 'dron':
        collection = db.get_collection('drones')
    else:
        collection = db.get_collection('robots')
    count = 0
    mensaje = "No available devices"
    fecha_manana = datetime.now() + timedelta(days=1)
    fecha_manana = fecha_manana.strftime("%Y-%m-%d")
    if fecha < fecha_manana:
        return False, "Date is not available"
    
    for data in collection.find():
        if data['status'] != 'maintenance' and data['status'] != 'retired':
            if fecha in data['reservations']:
                if hora not in data['reservations'][fecha]:
                    tmp = data['reservations'][fecha]
                    tmp.append(hora)
                    collection.update_one({'_id': data['_id']}, {"$set": {"reservations.{0}".format(fecha): tmp}})
                    count += 1
                    break
            else:
                collection.update_one({'_id': data['_id']}, {"$set": {"reservations.{0}".format(fecha): [hora]}})
                count += 1
                break
    
    if count == 0:
        return False, mensaje

    collection = db.get_collection('historial')
    collection.insert_one({
        "device": data['name'], 
        "date": fecha, 
        "time": hora, 
        "destination": destino, 
        "product": producto, 
        "weight": peso, 
        "emit": name1, 
        "receive": name2, 
        "phone1": phone1, 
        "phone2": phone2, 
        "email1": email1, 
        "email2": email2
    })

    asunto_confirmacion = "Confirmación de Reserva"
    cuerpo_confirmacion = f"""
    Hola {name1},
    
    Su reserva ha sido confirmada.
    Dispositivo: {dispositivo}
    Fecha: {fecha}
    Hora: {hora}
    Destino: {destino}
    Producto: {producto}
    Peso: {peso}
    Nombre del destinatario: {name2}
    Teléfono del destinatario: {phone2}
    
    Gracias por usar nuestro servicio.
    """

    asunto_notificacion = "Notificación de Entrega"
    cuerpo_notificacion = f"""
    Hola {name2},
    
    Se le hará una entrega con los siguientes datos:
    Dispositivo: {dispositivo}
    Fecha: {fecha}
    Hora: {hora}
    Destino: {destino}
    Producto: {producto}
    Peso: {peso}
    Nombre del Emisor: {name1}
    Teléfono del Emisor: {phone1}
    Correo del Emisor: {email1}
    
    Gracias por usar nuestro servicio.
    """

    enviar_correo(email1, asunto_confirmacion, cuerpo_confirmacion)
    enviar_correo(email2, asunto_notificacion, cuerpo_notificacion)

    return True, "Successfully reserved"

def get_all_devices():
    db = client.get_database('ProcesosFinal')
    drones_collection = db.get_collection('drones')
    robots_collection = db.get_collection('robots')
    
    drones = list(drones_collection.find())
    robots = list(robots_collection.find())
    
    return drones, robots

def get_order_history():
    db = client.get_database('ProcesosFinal')
    history_collection = db.get_collection('historial')
    
    orders = list(history_collection.find())
    
    return orders