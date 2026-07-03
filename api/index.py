from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime, timedelta

app = Flask(__name__)

# 🌟 စနစ်စဖွင့်ကတည်းက Lahiri Ayanamsa စနစ်ကို သတ်မှတ်ထားခြင်း
swe.set_sid_mode(swe.SIDM_LAHIRI)

@app.route('/api/calc', methods=['GET'])
def calculate():
    try:
        dob = request.args.get('dob')  # YYYY-MM-DD
        tob = request.args.get('tob', '12:00')  # HH:MM
        
        if not dob:
            return jsonify({'error': 'Date of birth is required'}), 400

        # ၁။ မြန်မာစံတော်ချိန် (+6:30) မှ UTC/GMT သို့ တိကျသေချာစွာ ပြောင်းလဲခြင်း
        # မွေးချိန် မနက်စောစော ဖြစ်ပါက ရက်စွဲပါ အလိုအလျောက် နောက်တစ်ရက် ဆုတ်ပေးရန် datetime သုံးထားပါသည်
        local_time = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
        utc_time = local_time - timedelta(hours=6, minutes=30)

        # ၂။ Julian Day (Universal Time) ကို တိကျစွာ တွက်ချက်ခြင်း
        decimal_hour_utc = utc_time.hour + utc_time.minute / 60.0 + utc_time.second / 3600.0
        jd_ut = swe.julday(utc_time.year, utc_time.month, utc_time.day, decimal_hour_utc)

        # 🌍 ၃။ မွေးဖွားရာဒေသ တည်နေရာသတ်မှတ်ခြင်း 
        # (ဆရာ့ဇာတာအတွက် မြိတ်မြို့ တည်နေရာ Coordinates ဖြစ်ပါသည်)
        lat = 12.4333   # Latitude
        lon = 98.6167   # Longitude

        # 🔮 ၄။ ဂြိုဟ်များ၏ တည်နေရာကို Lahiri Ayanamsa နှုတ်ပြီး Sidereal အတိုင်းတွက်ခြင်း
        # (swe.FLG_SIDEREAL အလံကို သေသေချာချာ သုံးထားပါသည်)
        planets = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
            'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
            'Venus': swe.VENUS, 'Saturn': swe.SATURN
        }
        
        res = {}
        for name, p_id in planets.items():
            pos = swe.calc_ut(jd_ut, p_id, swe.FLG_SIDEREAL)[0][0]
            res[name] = round(pos, 2)

        # ရာဟု နှင့် ကိတ် တည်နေရာ (Sidereal Mode)
        rahu_pos = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
        res['Rahu'] = round(rahu_pos, 2)
        res['Ketu'] = round((rahu_pos + 180) % 360, 2)

        # 🎯 ၅။ လဂ် (Ascendant) ကို အိမ်စနစ်အလိုက် နိဂုဏ်းစနစ်စစ်စစ်ဖြင့် တွက်ချက်ခြင်း
        # (swe.FLG_SIDEREAL ကို သုံးထားသဖြင့် ကမ္ဘာ့တည်နေရာနှင့် အချိန်အလိုက် ပြိဿလဂ်သို့ ရောက်ရှိပါမည်)
        # b'P' သည် Placidus House System ဖြစ်ပါသည်
        ascmc, houses = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)
        
        # လဂ်ဒီဂရီကို ရယူခြင်း
        res['Ascendant'] = round(ascmc[0], 2)

        return jsonify({'positions': res})

    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Vercel Deployment အတွက်
app = app
