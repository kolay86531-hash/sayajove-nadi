from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime, timedelta
import math

app = Flask(__name__)

# 🌟 Lahiri Ayanamsa စနစ်
swe.set_sid_mode(swe.SIDM_LAHIRI)

# မြို့ကြီးများ ဒေတာဘေ့စ်
CITY_DB = {
    "ရန်ကုန်": {"lat": 16.8409, "lon": 96.1735},
    "မန္တလေး": {"lat": 21.9588, "lon": 96.0891},
    "နေပြည်တော်": {"lat": 19.7633, "lon": 96.0785},
    "တောင်ကြီး": {"lat": 20.7888, "lon": 97.0333},
    "မြိတ်": {"lat": 12.4333, "lon": 98.6167},
    "ထားဝယ်": {"lat": 14.0833, "lon": 98.2000},
    "ကော့သောင်း": {"lat": 9.9833, "lon": 98.5500},
    "ပုသိမ်": {"lat": 16.7833, "lon": 94.7333},
    "မော်လမြိုင်": {"lat": 16.4905, "lon": 97.6282},
    "စစ်တွေ": {"lat": 20.1436, "lon": 92.8958},
    "မြစ်ကြီးနား": {"lat": 25.3833, "lon": 97.4000}
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
        city_input = request.args.get('city', '').strip()
        
        if not dob: return jsonify({'error': 'Date of birth is required'}), 400

        # မြို့တည်နေရာ
        city_data = CITY_DB.get(city_input, {"lat": 16.8409, "lon": 96.1735})
        lat, lon = city_data["lat"], city_data["lon"]
        current_city = city_input if city_input in CITY_DB else "ရန်ကုန် (စံတော်ချိန်)"

        # UTC ပြောင်းခြင်း
        local_time = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
        utc_time = local_time - timedelta(hours=6, minutes=30)
        jd_ut = swe.julday(utc_time.year, utc_time.month, utc_time.day, utc_time.hour + utc_time.minute / 60.0)

        # ဂြိုဟ်တွက်ချက်ခြင်း
        planets = {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS, 'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 'Venus': swe.VENUS, 'Saturn': swe.SATURN}
        res, chart = {}, {}
        
        for name, p_id in planets.items():
            pos = swe.calc_ut(jd_ut, p_id, swe.FLG_SIDEREAL)[0][0]
            res[name] = round(pos, 2)
            chart[name] = {'house': int(pos // 30), 'degree': pos % 30}

        # Rahu/Ketu
        rahu_pos = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
        res['Rahu'], chart['Rahu'] = round(rahu_pos, 2), {'house': int(rahu_pos // 30), 'degree': rahu_pos % 30}
        ketu_pos = (rahu_pos + 180) % 360
        res['Ketu'], chart['Ketu'] = round(ketu_pos, 2), {'house': int(ketu_pos // 30), 'degree': ketu_pos % 30}

        # Ascendant
        ascmc, _ = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)
        res['Ascendant'] = round(ascmc[0], 2)
        chart['Ascendant'] = {'house': int(ascmc[0] // 30), 'degree': ascmc[0] % 30}

        # --- နဒီ Math Functions ---
        def is_aspect(p1, p2):
            diff = (chart[p2]['house'] - chart[p1]['house'] + 12) % 12
            return diff in [0, 4, 8, 2, 6, 10]

        def is_interchange(p1, p2):
            return (chart[p1]['house'] in OWNERS.get(p2, [])) and (chart[p2]['house'] in OWNERS.get(p1, []))

        def get_dist_from_jupiter(planet):
            return (chart[planet]['house'] - chart['Jupiter']['house'] + 12) % 12 + 1

        def is_shakata_pos():
            dist = (chart['Moon']['house'] - chart['Jupiter']['house'] + 12) % 12 + 1
            return dist in [6, 8]

        def is_kala_sarpa_yoga():
            r, k = chart['Rahu']['house'], chart['Ketu']['house']
            planets_list = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
            c = 0
            for p in planets_list:
                h = chart[p]['house']
                if (r < k and r < h < k) or (r > k and (h > r or h < k)): c += 1
            return c == 7 or (len(planets_list) - c) == 7

        def get_transit_effect(p_transit, p_natal):
            if p_transit not in res or p_natal not in chart: return None
            t_house = int(res[p_transit] // 30)
            n_house = chart[p_natal]['house']
            dist = (t_house - n_house + 12) % 12
            if dist == 0: return f"<b>ကောဇာ {p_transit} ဖြတ်သန်းခြင်း:</b> ယခုလက်ရှိ {p_transit} သည် မူလ {p_natal} အိမ်ကို ဖြတ်သန်းနေသည်။ လုပ်ငန်းဆောင်တာများတွင် ရုတ်တရက် အပြောင်းအလဲများ ဖြစ်ပေါ်တတ်သည်။"
            if dist == 3: return f"<b>ကောဇာ {p_transit} အကျိုးပေး:</b> ကောဇာ {p_transit} သည် မူလ {p_natal} အိမ်မှ ၄ တန့်သို့ ရောက်ရှိနေသဖြင့် အိမ်၊ ခြံ၊ မြေကိစ္စများ အဆင်ပြေမည်။"
            return None

        # --- effects စာရင်း ---
        effects = [
            {"cat": "fortune", "check": is_aspect('Jupiter', 'Venus') and is_aspect('Jupiter', 'Mercury'), "text": "<b>ဓနသိဒ္ဓိယောဂ:</b> ငွေကြေးကံ အလွန်ကောင်းမွန်ပြီး ပညာရှိများ၏ အကူအညီ ရရှိမည်။"},
            {"cat": "fortune", "check": is_aspect('Sun', 'Jupiter'), "text": "<b>တနင်္ဂနွေ+ကြာသပတေး:</b> အစိုးရ သို့မဟုတ် အကြီးအကဲများ၏ အထောက်အပံ့ ရရှိမည်။"},
            {"cat": "fortune", "check": is_aspect('Jupiter', 'Venus'), "text": "<b>ကြာသပတေး+သောကြာ:</b> ကြီးပွားချမ်းသာမည့် ဇာတာရှင်ဖြစ်သည်။ အိမ်၊ ခြံ၊ မြေ ကံကောင်းတတ်သည်။"},
            {"cat": "fortune", "check": is_shakata_pos(), "text": "<b>သကပ်ယုဂ် (Shakata Yoga):</b> ဘဝသည် တက်လိုက်၊ ကျလိုက်နှင့် လှည်းဘီးကဲ့သို့ အလှည့်အပြောင်း ကြုံရတတ်သည်။"},
            {"cat": "fortune", "check": is_kala_sarpa_yoga(), "text": "<b>ကာလသရ္ပယုဂ်:</b> ဘဝတွင် အတိုက်အခံများ ကြုံရတတ်သော်လည်း ဒုတိယပိုင်းတွင် အံ့ဩဖွယ်ရာ အောင်မြင်မှု ရတတ်သည်။"},
            {"cat": "career", "check": is_aspect('Saturn', 'Jupiter'), "text": "<b>စနေ+ကြာသပတေး:</b> အလုပ်အကိုင်တွင် ဆရာတစ်ဆူ ဖြစ်တတ်သည်။ တာဝန်ကြီးသော ရာထူးများ ရတတ်သည်။"},
            {"cat": "spiritual", "check": is_aspect('Jupiter', 'Ketu'), "text": "<b>ကြာသပတေး+ကိတ်:</b> တရားထူး၊ တရားမြတ်များ ရရှိတတ်သည်။"},
            
            # အသစ်ပေါင်းထည့်ထားသော ယောဂများ
            {"cat": "fortune", "check": is_aspect('Sun', 'Mars'), "text": "<b>ပရဏယောဂ (အာဏာယောဂ):</b> သတ္တိဗျတ္တိနှင့် ပြည့်စုံသူ ဖြစ်သည်။ ခေါင်းဆောင်မှုနေရာတွင် အလွန်ထူးချွန်သည်။"},
            {"cat": "fortune", "check": is_aspect('Moon', 'Venus'), "text": "<b>လက္ခဏယောဂ (အနုပညာယောဂ):</b> စိတ်ကူးယဉ်ဆန်ပြီး အနုပညာကို အလွန်နှစ်သက်သူဖြစ်သည်။"},
            {"cat": "career", "check": is_aspect('Mercury', 'Rahu'), "text": "<b>ဗုဒ္ဓဟူး+ရာဟု (နည်းပညာယောဂ):</b> ကွန်ပျူတာ၊ နည်းပညာ၊ စာရင်းအင်း သို့မဟုတ် သုတေသနလုပ်ငန်းများတွင် အထူးအောင်မြင်မည်။"},
            {"cat": "spiritual", "check": is_aspect('Saturn', 'Jupiter') and is_aspect('Jupiter', 'Ketu'), "text": "<b>မဟာဝိဇ္ဇာယောဂ:</b> ဝိညာဉ်ရေးရာ ပညာရပ်များတွင် ထူးခြားသော အသိဉာဏ် ရရှိတတ်သည်။"},
            
            # ကောဇာဟောချက်များ
            {"cat": "fortune", "check": get_transit_effect('Jupiter', 'Moon') is not None, "text": f"{get_transit_effect('Jupiter', 'Moon')}"},
            {"cat": "career", "check": get_transit_effect('Saturn', 'Sun') is not None, "text": f"{get_transit_effect('Saturn', 'Sun')}"}
        ]

        # HTML ပြန်ထုတ်ခြင်း
        result_html = f"<div>📍 တွက်ချက်ပေးသောမြို့ - <b>{current_city}</b></div>"
        has_yoga = False
        for cat in ["fortune", "career", "marriage", "family", "spiritual"]:
            filtered = [e for e in effects if e["cat"] == cat and e["check"]]
            if filtered:
                has_yoga = True
                result_html += f"<h3>{cat}</h3>"
                for f in filtered: result_html += f"<p>{f['text']}</p>"

        return jsonify({'positions': res, 'result_html': result_html})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
