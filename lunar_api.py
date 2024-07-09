from flask import Flask, jsonify, request
from datetime import datetime
from swisseph import swe, SwissEph
import pytz
from geopy.geocoders import Nominatim

app = Flask(__name__)
geolocator = Nominatim(user_agent="lunar_api")
swe = SwissEph()

# Inicialización de Swiss Ephemeris
swe = swe

# Función para obtener el signo lunar y el grado
def calculate_moon_sign_degree(observer):
    jul_day_ut = swe.julday(observer.year, observer.month, observer.day, observer.hour)
    planet_num = swe.MOON
    flag = swe.FLG_SPEED
    res = swe.calc_ut(jul_day_ut, planet_num, flag)
    
    moon_longitude = res[0]  # Longitud de la Luna en grados
    moon_sign_degree = moon_longitude % 30  # Grado dentro del signo lunar
    moon_sign = swe.get_planet_name(swe.get_ayanamsa(jul_day_ut))  # Signo lunar

    return moon_sign, moon_sign_degree

# Función para obtener la fase lunar
def get_lunar_phase(date_time):
    jul_day_ut = swe.julday(date_time.year, date_time.month, date_time.day, date_time.hour)
    phase = swe.calc_ut(jul_day_ut, swe.MOON, swe.FLG_EQUATORIAL)[2]

    return phase

# Función para obtener el texto de la fase lunar según el hemisferio
def get_moon_phase_text(lunar_phase, hemisphere):
    if hemisphere == 'north':
        phases = [
            (0, 'Luna Nueva'),
            (45, 'Luna Creciente'),
            (90, 'Cuarto Creciente'),
            (135, 'Gibosa Creciente'),
            (180, 'Luna Llena'),
            (225, 'Gibosa Menguante'),
            (270, 'Cuarto Menguante'),
            (315, 'Luna Menguante'),
            (360, 'Luna Nueva')
        ]
    else:
        phases = [
            (0, 'Luna Nueva'),
            (45, 'Luna Menguante'),
            (90, 'Cuarto Menguante'),
            (135, 'Gibosa Menguante'),
            (180, 'Luna Llena'),
            (225, 'Gibosa Creciente'),
            (270, 'Cuarto Creciente'),
            (315, 'Luna Creciente'),
            (360, 'Luna Nueva')
        ]

    for angle, phase in phases:
        if lunar_phase < angle:
            return phase
    return 'Desconocida'

# Función para determinar si la luna está ascendente o descendente
def is_moon_ascending(observer):
    sun = swe.calc_ut(swe.julday(observer.year, observer.month, observer.day, observer.hour), swe.SUN)
    houses = swe.houses(swe.julday(observer.year, observer.month, observer.day, observer.hour), observer.lat, observer.lon, b'P')[0]
    moon_house = swe.house_pos(swe.julday(observer.year, observer.month, observer.day, observer.hour), observer.lat, observer.lon, swe.MOON)[0]
    ascendant = swe.houses(swe.julday(observer.year, observer.month, observer.day, observer.hour), observer.lat, observer.lon, b'P')[1].split('#')[0]
    moon_ascending = moon_house > ascendant
    return moon_ascending

@app.route('/lunar_info', methods=['GET'])
def lunar_info():
    try:
        # Obtener la fecha y hora desde el parámetro de la solicitud o usar la fecha y hora actual
        datetime_str = request.args.get('datetime', datetime.now().strftime('%Y-%m-%dT%H:%M'))
        date_time = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
        
        # Obtener la ubicación desde el parámetro de la solicitud
        location_name = request.args.get('location', 'Greenwich')
        
        # Usar geopy para obtener las coordenadas de la ubicación
        location = geolocator.geocode(location_name)
        
        if not location:
            return jsonify({'error': 'Location not found'}), 400
        
        # Crear un objeto de ubicación de observador para Swiss Ephemeris
        observer = {
            'year': date_time.year,
            'month': date_time.month,
            'day': date_time.day,
            'hour': date_time.hour,
            'lat': location.latitude,
            'lon': location.longitude,
        }
        
        # Calcular la fase lunar
        lunar_phase = get_lunar_phase(date_time)
        lunar_phase_text = get_moon_phase_text(lunar_phase, 'north')  # Se asume hemisferio norte por defecto
        
        # Calcular el signo lunar y el grado del signo lunar
        moon_sign, moon_sign_degree = calculate_moon_sign_degree(observer)
        
        # Determinar si la luna está ascendente o descendente
        moon_ascending = is_moon_ascending(observer)
        
        # Crear respuesta JSON
        response = {
            'datetime': date_time.strftime('%Y-%m-%dT%H:%M'),
            'location': location_name,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'lunar_phase': round(lunar_phase, 2),
            'lunar_phase_text': lunar_phase_text,
            'lunar_sign': moon_sign,
            'moon_sign_degree': round(moon_sign_degree, 2),
            'moon_ascending': moon_ascending,
        }
        
        return jsonify(response)
    
    except Exception as e:
        response = {
            'error': str(e)
        }
        return jsonify(response), 400

# Ruta para cargar la página inicial
@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)


