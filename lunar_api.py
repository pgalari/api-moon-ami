from flask import Flask, jsonify, request, render_template
from datetime import datetime
import swisseph as swe
from geopy.geocoders import Nominatim
import pytz

app = Flask(__name__)

def get_moon_phase_text(lunar_phase):
    phase_texts = [
        'Luna Nueva', 'Luna Creciente', 'Cuarto Creciente', 'Gibosa Creciente',
        'Luna Llena', 'Gibosa Menguante', 'Cuarto Menguante', 'Luna Menguante'
    ]
    return phase_texts[lunar_phase]

def calculate_moon_sign(jd):
    moon_pos = swe.calc_ut(jd, swe.MOON)
    moon_longitude = moon_pos[0]

    constellations = [
        ('Aries', 0, 30), ('Tauro', 30, 60), ('Géminis', 60, 90),
        ('Cáncer', 90, 120), ('Leo', 120, 150), ('Virgo', 150, 180),
        ('Libra', 180, 210), ('Escorpio', 210, 240), ('Sagitario', 240, 270),
        ('Capricornio', 270, 300), ('Acuario', 300, 330), ('Piscis', 330, 360)
    ]
    moon_sign = next(sign for sign, start, end in constellations if start <= moon_longitude < end)
    sign_degree = moon_longitude % 30

    return moon_sign, round(sign_degree, 2)

@app.route('/')
def index():
    return render_template('index.html')

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

        jd = swe.julday(date_time.year, date_time.month, date_time.day, date_time.hour + date_time.minute / 60.0)
        moon_sign, sign_degree = calculate_moon_sign(jd)

        sun_pos = swe.calc_ut(jd, swe.SUN)
        phase_angle = (swe.calc_ut(jd, swe.MOON)[0] - sun_pos[0]) % 360
        lunar_phase = (phase_angle / 45) % 8
        lunar_phase = round(lunar_phase)

        lunar_phase_text = get_moon_phase_text(lunar_phase)

        response = {
            'datetime': date_time.strftime('%d-%m-%Y %H:%M'),
            'location': location_name,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'lunar_phase': lunar_phase,
            'lunar_phase_text': lunar_phase_text,
            'lunar_sign': moon_sign,
            'moon_ascending': True,
            'moon_sign_degree': sign_degree
        }

        return jsonify(response)

    except Exception as e:
        response = {
            'error': str(e)
        }
        return jsonify(response), 400

if __name__ == '__main__':
    app.run(debug=True)


