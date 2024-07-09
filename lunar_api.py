from flask import Flask, jsonify, request
from datetime import datetime
import ephem
from astral import moon, LocationInfo
from geopy.geocoders import Nominatim
import pytz
import os

app = Flask(__name__)

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

def is_moon_ascending(observer, moon_obj):
    sun = ephem.Sun(observer)
    return moon_obj.ra > sun.ra

def calculate_moon_sign(observer):
    moon_obj = ephem.Moon(observer)
    moon_obj.compute(observer)
    moon_longitude = moon_obj.hlon * 180.0 / ephem.pi
    
    constellations = [
        ('Aries', 0, 30), ('Tauro', 30, 60), ('Géminis', 60, 90),
        ('Cáncer', 90, 120), ('Leo', 120, 150), ('Virgo', 150, 180),
        ('Libra', 180, 210), ('Escorpio', 210, 240), ('Sagitario', 240, 270),
        ('Capricornio', 270, 300), ('Acuario', 300, 330), ('Piscis', 330, 360)
    ]

    for sign, start, end in constellations:
        if start <= moon_longitude < end:
            degree_in_sign = moon_longitude - start
            return sign, degree_in_sign
    return 'Desconocida', 0

@app.route('/')

@app.route('/lunar_info', methods=['GET'])
def lunar_info():
    try:
        datetime_str = request.args.get('datetime', datetime.now().strftime('%d-%m-%Y %H:%M'))
        date_time = datetime.strptime(datetime_str, '%d-%m-%Y %H:%M')
        
        location_name = request.args.get('location', 'Greenwich')
        
        geolocator = Nominatim(user_agent="lunar_api")
        location = geolocator.geocode(location_name)
        
        if not location:
            return jsonify({'error': 'Ubicación no encontrada'}), 400
        
        city_location = LocationInfo(name=location_name, region='', timezone='UTC', latitude=location.latitude, longitude=location.longitude)
        
        lunar_phase = moon.phase(date_time)
        
        observer = ephem.Observer()
        observer.lat, observer.lon = str(location.latitude), str(location.longitude)
        observer.date = date_time
        
        moon_obj = ephem.Moon(observer)
        
        hemisphere = 'north' if float(location.latitude) > 0 else 'south'
        lunar_phase_text = get_moon_phase_text(lunar_phase, hemisphere)
        moon_sign, moon_sign_degree = calculate_moon_sign(observer)
        moon_ascending = is_moon_ascending(observer, moon_obj)
        
        response = {
            'datetime': date_time.strftime('%d-%m-%Y %H:%M'),
            'location': location_name,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'lunar_phase': round(lunar_phase, 2),
            'lunar_phase_text': lunar_phase_text,
            'lunar_sign': moon_sign,
            'moon_sign_degree': round(moon_sign_degree, 2),
            'moon_ascending': moon_ascending
        }
        
        return jsonify(response)
    
    except Exception as e:
        response = {
            'error': str(e)
        }
        return jsonify(response), 400

if __name__ == '__main__':
    app.run(debug=True)
