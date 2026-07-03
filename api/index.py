from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import swisseph as swe
import os

app = Flask(__name__)

# Lahiri Ayanamsa စနစ် သတ်မှတ်ခြင်း
swe.set_sid_mode(swe.SIDM_LAHIRI)

# 🔑 ဆရာ့ဖက်က သတ်မှတ်မည့် လျှို့ဝှက်ဆားဗစ်သင်္ကေတ (App ဘက်နှင့် တူရပါမည်)
SECRET_SALT = 8491

# 🌍 မြန်မာနိုင်ငံ မြို့ကြီးအချို့၏ Lat/Lon Database (ကျောင်းသား ရိုက်ထည့်လိုက်သော မြို့အလိုက် တွက်ရန်)
CITY_DB = {
    "မြိတ်": {"lat": 12.4333, "lon": 98.6167},
    "ရန်ကုန်": {"lat": 16.8661, "lon": 96.1951},
    "မန္တလေး": {"lat": 21.9588, "lon": 96.0891},
    "နေပြည်တော်": {"lat": 19.7450, "lon": 96.1297},
    "ပဲခူး": {"lat": 17.3333, "lon": 96.4833},
    "မော်လမြိုင်": {"lat": 16.4905, "lon": 97.6282}
}

@app.route('/api/calc', methods=['GET'])
def calculate():
    try:
        # --- (၁) လိုင်စင် Key စစ်ဆေးခြင်း အပိုင်း ---
        # ကျောင်းသားထံမှ License Key နှင့် Device ID ကို တောင်းခံစစ်ဆေးခြင်း
        license_key = request.args.get('license_key', '').strip().upper()
        device_id = request.args.get('device_id', '').strip().upper()
        
        # လိုင်စင်စနစ်သုံးရန် ကုဒ်ဖွင့်ထားခြင်း (အကယ်၍ လိုင်စင်စနစ် မစမ်းချင်သေးပါက လိုင်း ၃ ကြောင်းကို ပိတ်ထားနိုင်ပါသည်)
        # expected_key = f"KEY-{int(device_id.replace('JOVE-', '')) * 3 + SECRET_SALT}"
        # if license_key != expected_key:
        #     return jsonify({'error': 'Invalid or expired license key.'}), 403

        # --- (၂) ဗေဒင်တွက်ချက်ခြင်း အပိုင်း ---
        dob = request.args.get('dob')  # YYYY-MM-DD
        tob = request.args.get('tob', '12:00')  # HH:MM
        city_name = request.args.get('city', 'မြိတ်').strip()

        if not dob:
            return jsonify({'error': 'Date of birth is required'}), 400

        # မြို့အလိုက် တည်နေရာရှာဖွေခြင်း (မတွေ့ပါက မူလ မြိတ်မြို့ တည်နေရာအတိုင်း ယူမည်)
        geo = CITY_DB.get(city_name, {"lat": 12.4333, "lon": 98.6167})
        lat = geo["lat"]
        lon = geo["lon"]

        # Python Datetime သုံးပြီး မြန်မာစံတော်ချိန် (+6:30) မှ UTC သို့ တိကျစွာ ပြောင်းလဲခြင်း
        local_time = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
        utc_time = local_time - timedelta(hours=6, minutes=30)

        # Julian Day ဂဏန်းတွက်ချက်ခြင်း
        decimal_hour_utc = utc_time.hour + utc_time.minute / 60.0
        jd = swe.julday(utc_time.year, utc_time.month, utc_time.day, decimal_hour_utc)

        # ဂြိုဟ်တည်နေရာများ တွက်ချက်ခြင်း (Sidereal Flag သုံးထားပါသည်)
        planets = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
            'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
            'Venus': swe.VENUS, 'Saturn': swe.SATURN
        }
        
        res = {}
        for name, p_id in planets.items():
            pos = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)[0][0]
            res[name] = round(pos, 2)

        # ရာဟု နှင့် ကိတ် တည်နေရာ
        rahu_pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
        res['Rahu'] = round(rahu_pos, 2)
        res['Ketu'] = round((rahu_pos + 180) % 360, 2)

        # 🎯 ပြင်ဆင်လိုက်သည့်နေရာ: လဂ် (Ascendant) တွက်ချက်ရာတွင် swe.FLG_SIDEREAL ထည့်သွင်းပေးခြင်း
        # swe.houses_ex တွင် ရှေ့ဆုံးမှ Flag အဖြစ် swe.FLG_SIDEREAL ကို ထည့်မှသာ Lahiri လဂ် အမှန်ထွက်ပါမည်
        ascmc, houses = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        res['Ascendant'] = round(ascmc[0], 2)

        return jsonify({'positions': res})

    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Vercel အတွက် app variable ကို expose လုပ်ထားရန်
app = app
