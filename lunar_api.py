from flask import Flask, jsonify, request, render_template
from datetime import datetime
import swisseph as swe
from geopy.geocoders import Nominatim
import os
import pytz

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lunar_info', methods=['GET'])
def lunar_info():
    try:
        # Obtener la fecha y hora desde el parámetro de la solicitud o usar la fecha y hora actual
        datetime_str = request.args.get('datetime', datetime.now().strftime('%d-%m-%Y %H:%M'))
        date_time = datetime.strptime(datetime_str, '%d-%m-%Y %H:%M')

        # Obtener la ubicación desde el parámetro de la solicitud
        location_name = request.args.get('location', 'Greenwich')

        # Usar geopy para obtener las coordenadas de la ubicación
        geolocator = Nominatim(user_agent="lunar_api")
        location = geolocator.geocode(location_name)

        if not location:
            return jsonify({'error': 'Ubicación no encontrada'}), 400

        # Calcular la fase lunar y signo lunar usando Swiss Ephemeris
        jd = swe.julday(date_time.year, date_time.month, date_time.day, date_time.hour + date_time.minute / 60.0)
        moon_pos = swe.calc_ut(jd, swe.MOON)
        moon_longitude = moon_pos[0]

        # Definir los signos zodiacales y sus rangos en grados
        constellations = [
            ('Aries', 0, 30), ('Tauro', 30, 60), ('Géminis', 60, 90),
            ('Cáncer', 90, 120), ('Leo', 120, 150), ('Virgo', 150, 180),
            ('Libra', 180, 210), ('Escorpio', 210, 240), ('Sagitario', 240, 270),
            ('Capricornio', 270, 300), ('Acuario', 300, 330), ('Piscis', 330, 360)
        ]
        moon_sign = next(sign for sign, start, end in constellations if start <= moon_longitude < end)

        # Calcular el grado del signo lunar
        sign_degree = moon_longitude % 30

        # Calcular la fase lunar (simplificada)
        sun_pos = swe.calc_ut(jd, swe.SUN)
        phase_angle = (moon_longitude - sun_pos[0]) % 360
        lunar_phase = (phase_angle / 45) + 1
        lunar_phase = round(lunar_phase % 8)

        phase_texts = [
            'Luna Nueva', 'Luna Creciente', 'Cuarto Creciente', 'Gibosa Creciente',
            'Luna Llena', 'Gibosa Menguante', 'Cuarto Menguante', 'Luna Menguante'
        ]
        lunar_phase_text = phase_texts[lunar_phase]

        # Crear respuesta JSON
        response = {
            'datetime': date_time.strftime('%d-%m-%Y %H:%M'),
            'location': location_name,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'lunar_phase': lunar_phase,
            'lunar_phase_text': lunar_phase_text,
            'lunar_sign': moon_sign,
            'moon_ascending': True,  # Simplificación, necesitas calcularlo adecuadamente si es necesario
            'moon_sign_degree': round(sign_degree, 2)
        }

        return jsonify(response)

    except Exception as e:
        response = {
            'error': str(e)
        }
        return jsonify(response), 400

if __name__ == '__main__':
    app.run(debug=True)

