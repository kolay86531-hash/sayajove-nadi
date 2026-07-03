 from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime, timedelta

app = Flask(__name__)

# Lahiri Ayanamsa စနစ်
swe.set_sid_mode(swe.SIDM_LAHIRI)

# မြို့ကြီးများ
CITY_DB = {
    "ရန်ကုန်": {"lat": 16.8409, "lon": 96.1735},
    "မန္တလေး": {"lat": 21.9588, "lon": 96.0891},
    "နေပြည်တော်": {"lat": 19.7633, "lon": 96.0785},
    "တောင်ကြီး": {"lat": 20.7888, "lon": 97.0333},
    "မြိတ်": {"lat": 12.4333, "lon": 98.6167}
}

OWNERS = {
    'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
    'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
}

@app.route('/api/calc', methods=['GET'])
def calculate():
    try:
        dob = request.args.get('dob')
        tob = request.args.get('tob', '12:00')
        city_input = request.args.get('city', 'ရန်ကုန်')
        
        # UTC ပြောင်းခြင်း
        local_time = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
        utc_time = local_time - timedelta(hours=6, minutes=30)
        jd_ut = swe.julday(utc_time.year, utc_time.month, utc_time.day, utc_time.hour + utc_time.minute / 60.0)

        # ဂြိုဟ်တွက်ချက်ခြင်း
        city = CITY_DB.get(city_input, CITY_DB["ရန်ကုန်"])
        planets = {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS, 'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 'Venus': swe.VENUS, 'Saturn': swe.SATURN}
        res, chart = {}, {}
        
        for name, p_id in planets.items():
            pos = swe.calc_ut(jd_ut, p_id, swe.FLG_SIDEREAL)[0][0]
            res[name] = round(pos, 2)
            chart[name] = {'house': int(pos // 30)}

        # Rahu/Ketu
        r_pos = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
        res['Rahu'], chart['Rahu'] = round(r_pos, 2), {'house': int(r_pos // 30)}
        k_pos = (r_pos + 180) % 360
        res['Ketu'], chart['Ketu'] = round(k_pos, 2), {'house': int(k_pos // 30)}

        # --- Helper Functions ---
        def is_aspect(p1, p2):
            diff = (chart[p2]['house'] - chart[p1]['house'] + 12) % 12
            return diff in [0, 4, 8, 2, 6, 10]

        def get_transit_effect(p_transit, p_natal):
            if p_transit not in res or p_natal not in chart: return None
            dist = (int(res[p_transit] // 30) - chart[p_natal]['house'] + 12) % 12
            msgs = {0: "ဖြတ်သန်းနေသည်။ အပြောင်းအလဲများ ဖြစ်ပေါ်တတ်သည်။", 
                    3: "၄ တန့်သို့ ရောက်နေသည်။ အိမ်ခြံမြေကိစ္စ အဆင်ပြေမည်။",
                    6: "၇ တန့်သို့ ရောက်နေသည်။ အိမ်ထောင်ရေး/လုပ်ငန်းတွဲဖက် အကျိုးပေးမည်။",
                    9: "၁၀ တန့်သို့ ရောက်နေသည်။ လုပ်ငန်းခွင် အထူးအောင်မြင်မည်။"}
            return msgs.get(dist)

        # --- Effects စာရင်း (အပြည့်အစုံ) ---
        effects = [
            # နဒီယောဂများ
            {"cat": "fortune", "check": is_aspect('Jupiter', 'Venus'), "text": "<b>ဓနသိဒ္ဓိယောဂ:</b> ငွေကြေးဓန ပေါများမည်။ အိမ်၊ ခြံ၊ မြေ အမွေအနှစ် ရရှိတတ်သည်။"},
            {"cat": "fortune", "check": is_aspect('Sun', 'Mars'), "text": "<b>ပရဏယောဂ:</b> သတ္တိဗျတ္တိနှင့် ပြည့်စုံသည်။ ခေါင်းဆောင်မှုနေရာတွင် အလွန်ထူးချွန်သည်။"},
            {"cat": "fortune", "check": is_aspect('Moon', 'Venus'), "text": "<b>လက္ခဏယောဂ:</b> အနုပညာ ပါရမီရှင်။ အလှအပနှင့် ဖက်ရှင်လုပ်ငန်းများတွင် ထူးချွန်သည်။"},
            {"cat": "career", "check": is_aspect('Saturn', 'Jupiter'), "text": "<b>ဓမ္မကရ္မအဓိပတိယောဂ:</b> တာဝန်ယူတတ်သူဖြစ်ပြီး ဆရာ သို့မဟုတ် အကြံပေးပုဂ္ဂိုလ် ဖြစ်တတ်သည်။"},
            {"cat": "spiritual", "check": is_aspect('Jupiter', 'Ketu'), "text": "<b>ဝိဇ္ဇာယောဂ:</b> နက်နဲသော ပညာရပ်များကို သင်ယူတတ်သူဖြစ်သည်။ ဝိညာဉ်ရေးရာတွင် ထူးချွန်သည်။"},
            
            # ကောဇာဟောချက်များ
            {"cat": "fortune", "check": get_transit_effect('Jupiter', 'Moon'), "text": f"<b>ကောဇာ ကြာသပတေး:</b> {get_transit_effect('Jupiter', 'Moon')}"},
            {"cat": "career", "check": get_transit_effect('Saturn', 'Sun'), "text": f"<b>ကောဇာ စနေ:</b> {get_transit_effect('Saturn', 'Sun')}"},
            {"cat": "marriage", "check": get_transit_effect('Venus', 'Venus'), "text": f"<b>ကောဇာ သောကြာ:</b> {get_transit_effect('Venus', 'Venus')}"}
        ]

        # HTML ထုတ်ခြင်း
        html = f"<div>📍 တည်နေရာ - {city_input}</div>"
        for cat in ["fortune", "career", "marriage", "spiritual"]:
            items = [e['text'] for e in effects if e['cat'] == cat and e['check']]
            if items:
                html += f"<h3>{cat.capitalize()}</h3>" + "".join([f"<p>{i}</p>" for i in items])

        return jsonify({'html': html})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
