
from flask import Flask, request, jsonify
import swisseph as swe
import os

app = Flask(__name__)

# Lahiri Ayanamsa စနစ်
swe.set_sid_mode(swe.SIDM_LAHIRI)

@app.route('/api/calc', methods=['GET'])
def calculate():
    try:
        dob = request.args.get('dob')
        tob = request.args.get('tob', '12:00')

        if not dob:
            return jsonify({'error': 'Date of birth is required'}), 400

        y, m, d = map(int, dob.split('-'))
        hh, mm = map(int, tob.split(':'))

        # UTC ပြောင်းရန် (မြန်မာစံတော်ချိန် +6:30 မို့ 6.5 နှုတ်)
        dt_utc = hh + mm/60.0 - 6.5
        jd = swe.julday(y, m, d, dt_utc)

        planets = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
            'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
            'Venus': swe.VENUS, 'Saturn': swe.SATURN
        }

        res = {}
        for name, p_id in planets.items():
            pos = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)[0][0]
            res[name] = round(pos, 2)

        rahu_pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
        res['Rahu'] = round(rahu_pos, 2)
        res['Ketu'] = round((rahu_pos + 180) % 360, 2)

        # Myeik, Myanmar တည်နေရာ
        geopos = (98.6167, 12.4333, 0)
        ascmc = swe.houses_ex(jd, geopos[1], geopos[0], b'P')[0]
        res['Ascendant'] = round(ascmc[0], 2)

        return jsonify({'positions': res})

    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Vercel အတွက် app variable ကို expose လုပ်ထားရန်
app = app
