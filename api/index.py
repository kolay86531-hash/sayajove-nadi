from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime, timedelta

app = Flask(__name__)

# Lahiri Ayanamsa စနစ်
swe.set_sid_mode(swe.SIDM_LAHIRI)

CITY_DB = {
    "ရန်ကုန်": {"lat": 16.8409, "lon": 96.1735},
    "မန္တလေး": {"lat": 21.9588, "lon": 96.0891},
    "နေပြည်တော်": {"lat": 19.7633, "lon": 96.0785},
    "တောင်ကြီး": {"lat": 20.7888, "lon": 97.0333},
    "မြိတ်": {"lat": 12.4333, "lon": 98.6167}
}

@app.route('/api/calc', methods=['GET'])
def calculate():
    try:
        dob = request.args.get('dob')
        tob = request.args.get('tob', '12:00')
        city_input = request.args.get('city', 'ရန်ကုန်')
        
        local_time = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
        utc_time = local_time - timedelta(hours=6, minutes=30)
        jd_ut = swe.julday(utc_time.year, utc_time.month, utc_time.day, utc_time.hour + utc_time.minute / 60.0)

        planets = {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS, 'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 'Venus': swe.VENUS, 'Saturn': swe.SATURN}
        res, chart = {}, {}
        
        for name, p_id in planets.items():
            pos = swe.calc_ut(jd_ut, p_id, swe.FLG_SIDEREAL)[0][0]
            res[name] = round(pos, 2)
            chart[name] = {'house': int(pos // 30)}

        # Helper Functions
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

        # Dasha Logic
        moon_lon = res['Moon']
        nak_index = int(moon_lon / (360 / 27))
        dasha_order = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
        current_dasha = dasha_order[nak_index % 9]
        dasha_texts = {
            'Ketu': "ကိတ်သက်: စိတ်ရှုပ်ထွေးခြင်း၊ ဝိညာဉ်ရေးရာ စိတ်ဝင်စားခြင်း။", 'Venus': "သောကြာသက်: စီးပွားရေး ကံကောင်းခြင်း၊ အချစ်ရေး သာယာခြင်း။",
            'Sun': "တနင်္ဂနွေသက်: အာဏာ၊ ဂုဏ်သတင်းနှင့် အောင်မြင်မှုများ ရရှိမည်။", 'Moon': "တနင်္လာသက်: စိတ်ချမ်းသာခြင်း၊ မိသားစုနှင့် ပျော်ရွှင်ရခြင်း။",
            'Mars': "အင်္ဂါသက်: သတ္တိဗျတ္တိ တိုးတက်မည်၊ ဒေါသကို ထိန်းချုပ်ပါ။", 'Rahu': "ရာဟုသက်: ရုတ်တရက် အောင်မြင်ခြင်း၊ နိုင်ငံခြားခရီးများ အကျိုးပေးသည်။",
            'Jupiter': "ကြာသပတေးသက်: ပညာရေး၊ ဓမ္မရေးရာနှင့် ဘဝတိုးတက်မှုအတွက် ကောင်းမွန်သော ကာလဖြစ်သည်။",
            'Saturn': "စနေသက်: အလုပ်တွင် ဖိအားများမည်၊ ကြိုးစားလျှင် ရေရှည်အတွက် အကျိုးရှိမည်။", 'Mercury': "ဗုဒ္ဓဟူးသက်: စီးပွားရေး၊ ပညာရေး အလွန်အဆင်ပြေမည်။"
        }

        # Effects List
        effects = [
            {"cat": "dasha", "check": True, "text": f"<b>လက်ရှိဂြိုဟ်သက်:</b> {dasha_texts[current_dasha]}"},
            {"cat": "fortune", "check": is_aspect('Jupiter', 'Venus'), "text": "<b>ဓနသိဒ္ဓိယောဂ:</b> ငွေကြေးဓန ပေါများမည်။"},
            {"cat": "career", "check": is_aspect('Saturn', 'Jupiter'), "text": "<b>ဓမ္မကရ္မအဓိပတိယောဂ:</b> တာဝန်ယူတတ်သူဖြစ်ပြီး ဆရာ သို့မဟုတ် အကြံပေးပုဂ္ဂိုလ် ဖြစ်တတ်သည်။"},
            {"cat": "fortune", "check": get_transit_effect('Jupiter', 'Moon') is not None, "text": f"<b>ကောဇာ ကြာသပတေး:</b> {get_transit_effect('Jupiter', 'Moon')}"}
        ]

        # HTML ထုတ်ခြင်း
        html = f"<div>📍 တည်နေရာ - {city_input}</div>"
        # Dasha ကို အရင်ဆုံးပြစေရန်
        for cat in ["dasha", "fortune", "career", "marriage", "spiritual"]:
            items = [e['text'] for e in effects if e['cat'] == cat and e['check']]
            if items:
                html += f"<h3>{cat.capitalize()}</h3>" + "".join([f"<p>{i}</p>" for i in items])

        return jsonify({'html': html})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
