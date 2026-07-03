
from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime, timedelta

app = Flask(__name__)

# Lahiri Ayanamsa စနစ်
swe.set_sid_mode(swe.SIDM_LAHIRI)

# ဂြိုဟ်အိမ်ပိုင်ရှင်များ (အိမ်ဖလှယ်ခြင်း ယောဂ စစ်ဆေးရန်)
OWNERS = {
    'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
    'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
}

@app.route('/api/calc', methods=['GET'])
def calculate():
    try:
        dob = request.args.get('dob')  # YYYY-MM-DD
        tob = request.args.get('tob', '12:00')  # HH:MM
        
        if not dob:
            return jsonify({'error': 'Date of birth is required'}), 400

        # ၁။ UTC သို့ တိကျစွာ ပြောင်းလဲခြင်း
        local_time = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
        utc_time = local_time - timedelta(hours=6, minutes=30)

        # ၂။ Julian Day တွက်ချက်ခြင်း
        decimal_hour_utc = utc_time.hour + utc_time.minute / 60.0 + utc_time.second / 3600.0
        jd_ut = swe.julday(utc_time.year, utc_time.month, utc_time.day, decimal_hour_utc)

        # 🌍 ၃။ မြိတ်မြို့ တည်နေရာ Coordinates
        lat = 12.4333
        lon = 98.6167

        # 🔮 ၄။ ဂြိုဟ်တည်နေရာများ တွက်ချက်ခြင်း (Sidereal Mode)
        planets = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
            'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
            'Venus': swe.VENUS, 'Saturn': swe.SATURN
        }
        
        res = {}
        chart = {}  # နဒီအဟောတွက်ရန် ဂြိုဟ်များ၏ အိမ် (House) နှင့် ဒီဂရီ
        
        for name, p_id in planets.items():
            pos = swe.calc_ut(jd_ut, p_id, swe.FLG_SIDEREAL)[0][0]
            res[name] = round(pos, 2)
            chart[name] = {'house': int(pos // 30), 'degree': pos % 30}

        # ရာဟု နှင့် ကိတ် တည်နေရာ
        rahu_pos = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
        res['Rahu'] = round(rahu_pos, 2)
        chart['Rahu'] = {'house': int(rahu_pos // 30), 'degree': rahu_pos % 30}
        
        ketu_pos = (rahu_pos + 180) % 360
        res['Ketu'] = round(ketu_pos, 2)
        chart['Ketu'] = {'house': int(ketu_pos // 30), 'degree': ketu_pos % 30}

        # လဂ် (Ascendant) တွက်ချက်ခြင်း
        ascmc, houses = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)
        res['Ascendant'] = round(ascmc[0], 2)
        chart['Ascendant'] = {'house': int(ascmc[0] // 30), 'degree': ascmc[0] % 30}

        # ========================================================
        # 🔮 ၅။ နဒီဗေဒင် အဟော Logic များ (Nadi Yoga Calculation)
        # ========================================================
        
        # (က) သမ္ဗန် (Aspect) ရှိမရှိ စစ်ဆေးသည့် Function (၁၊ ၅၊ ၉၊ ၃၊ ၇၊ ၁၁ ရာသီအိမ်များ)
        def is_aspect(p1, p2):
            if p1 not in chart or p2 not in chart: return False
            diff = (chart[p2]['house'] - chart[p1]['house'] + 12) % 12
            return diff in [0, 4, 8, 2, 6, 10]

        # (ခ) ပရိဝတ္တန (Interchange) အိမ်ဖလှယ်ခြင်း ရှိမရှိ စစ်ဆေးသည့် Function
        def is_interchange(p1, p2):
            if p1 not in chart or p2 not in chart: return False
            p1_house = chart[p1]['house']
            p2_house = chart[p2]['house']
            return (p1_house in OWNERS.get(p2, [])) and (p2_house in OWNERS.get(p1, []))

        # (ဂ) ကြာသပတေးမှ ဂြိုဟ်တစ်ခုခု၏ အကွာအဝေးကို တွက်ချက်ခြင်း
        def get_dist_from_jupiter(planet):
            if 'Jupiter' not in chart or planet not in chart: return 0
            return (chart[planet]['house'] - chart['Jupiter']['house'] + 12) % 12 + 1

        # (ဃ) သကပ်ယုဂ် (Shakata Yoga) ရှိမရှိ စစ်ဆေးခြင်း
        def is_shakata_pos():
            dist = get_dist_from_jupiter('Moon')
            return dist in [6, 8]

        # (င) ကာလသရ္ပယုဂ် (Kala Sarpa Yoga) ရှိမရှိ စစ်ဆေးခြင်း
        def is_kala_sarpa_yoga():
            if 'Rahu' not in chart or 'Ketu' not in chart: return False
            r_pos = chart['Rahu']['house']
            k_pos = chart['Ketu']['house']
            planets_list = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
            count_cw = 0
            for p in planets_list:
                h = chart[p]['house']
                if (r_pos < k_pos and r_pos < h < k_pos) or (r_pos > k_pos and (h > r_pos or h < k_pos)):
                    count_cw += 1
            return count_cw == 7 or (len(planets_list) - count_cw) == 7

        # 📋 ဆရာ့မူလ နဒီအဟောကျမ်း ဒေတာဘေ့စ်
        effects = [
            {"cat": "family", "check": is_aspect('Moon', 'Rahu'), "text": "<b>တနင်္လာ+ရာဟု</b> မိခင်ဖြစ်သူမှာ ဇာတာရှင်မွေးစတွင် ကျန်းမာရေး အားနည်းတတ်ခြင်း သို့မဟုတ် Сိတ်သောက ရောက်တတ်သည်။"},
            {"cat": "career", "check": is_aspect('Saturn', 'Ketu'), "text": "<b>စနေ+ကိတ်</b> အလုပ်အကိုင်တွင် ရုတ်တရက် အပြောင်းအလဲများ သို့မဟုတ် ဝိညာဉ်ရေးရာနှင့် ပတ်သက်သော အလုပ်များ အကျိုးပေးမည်။"},
            {"cat": "fortune", "check": is_aspect('Jupiter', 'Venus') and is_aspect('Jupiter', 'Mercury'), "text": "<b>ဓနသိဒ္ဓိယောဂ</b> ငွေကြေးကံ အလွန်ကောင်းမွန်ပြီး ပညာရှိများ၏ အကူအညီ ရရှိမည်။"},
            {"cat": "marriage", "check": is_aspect('Venus', 'Ketu'), "text": "<b>သောကြာ+ကိတ်</b> အမျိုးသားဇာတာရှင်အတွက် အိမ်ထောင်ဖက်မှာ ဘာသာတရား ကိုင်းရှိုင်းသူ ဖြစ်တတ်သည်။ ဇနီးသည်နှင့် ဆက်ဆံရေး အေးစက်တတ်သည်။"},
            {"cat": "career", "check": is_interchange('Mars', 'Mercury'), "text": "<b>အင်္ဂါ+ဗုဒ္ဓဟူး (အိမ်ဖလှယ်ခြင်း)</b> စကားပြောဆိုရာတွင် အလွန်ထက်မြက်ပြီး နည်းပညာဖြင့် အောင်မြင်မည်။"},
            {"cat": "fortune", "check": is_aspect('Sun', 'Jupiter'), "text": "<b>တနင်္ဂနွေ+ကြာသပတေး</b> အစိုးရ သို့မဟုတ် အကြီးအကဲများ၏ အထောက်အပံ့ ရရှိမည်။"},
            {"cat": "fortune", "check": is_aspect('Jupiter', 'Venus'), "text": "<b>ကြာသပတေး+သောကြာ</b> ကြီးပွားချမ်းသာမည့် ဇာတာရှင်ဖြစ်သည်။ အိမ်၊ ခြံ၊ မြေ ကံကောင်းတတ်သည်။"},
            {"cat": "fortune", "check": is_aspect('Jupiter', 'Moon'), "text": "<b>ကြာသပတေး+တနင်္လာ</b> စိတ်သဘောထား နူးညံ့ပြီး ခရီးသွားခြင်းဖြင့် ကံကောင်းတတ်သည်။"},
            {"cat": "fortune", "check": is_aspect('Mercury', 'Venus'), "text": "<b>ဗုဒ္ဓဟူး+သောကြာ:</b> ပညာဉာဏ် ထက်မြက်ပြီး စီးပွားရေးတွင် အောင်မြင်မည်။"},
            {"cat": "career", "check": is_aspect('Saturn', 'Jupiter'), "text": "<b>စနေ+ကြာသပတေး</b> အလုပ်အကိုင်တွင် ဆရာတစ်ဆူ ဖြစ်တတ်သည်။ တာဝန်ကြီးသော ရာထူးများ ရရှိမည်။"},
            {"cat": "spiritual", "check": is_aspect('Jupiter', 'Ketu'), "text": "<b>ကြာသပတေး+ကိတ်</b> တရားထူး၊ တရားမြတ်များ ရရှိတတ်သည်။ လောကုတ္တရာ ပညာတွင် အလွန်ထူးချွန်မည်။"},
            {"cat": "spiritual", "check": is_aspect('Mercury', 'Ketu'), "text": "<b>ဗုဒ္ဓဟူး+ကိတ်</b> ဗေဒင်၊ နက္ခတ် သို့မဟုတ် လျှို့ဝှက်ပညာရပ်များကို အလိုလို သိမြင်တတ်သော ဉာဏ်ရှိသည်။"},
            {"cat": "fortune", "check": is_kala_sarpa_yoga(), "text": "<b>ကာလသရ္ပယုဂ် (Kala Sarpa Yoga)</b> ဘဝတွင် အတိုက်အခံများ ကြုံရတတ်သော်လည်း ဒုတိယပိုင်းတွင် အံ့ဩဖွယ်ရာ အောင်မြင်မှု ရတတ်သည်။"},
            {"cat": "fortune", "check": is_shakata_pos(), "text": "<b>သကပ်ယုဂ် (Shakata Yoga)</b> ဘဝသည် တက်လိုက်၊ ကျလိုက်နှင့် လှည်းဘီးကဲ့သို့ အလှည့်အပြောင်း ကြုံရတတ်သည်။"},
            {"cat": "spiritual", "check": get_dist_from_jupiter('Ketu') == 12, "text": "<b>မုတ္တိယုဂ် (Moksha Yoga)</b> ကိတ်သည် ၁၂ တန့်တွင် ရှိသဖြင့် ဝိညာဉ်ရေးရာနှင့် လွတ်မြောက်ရာလမ်းကို ရှာဖွေမည့်သူ ဖြစ်သည်။"}
        ]

        # ကဏ္ဍအလိုက် အဟောများကို HTML formats စုစည်းခြင်း
        cat_names = {"fortune": "ကံကြမ္မာ", "career": "အလုပ်အကိုင်", "marriage": "အိမ်ထောင်ရေး", "family": "မိသားစု", "spiritual": "ဝိညာဉ်ရေးရာ"}
        result_html = ""
        
        for cat_key, cat_name in cat_names.items():
            filtered = [f for f in effects if f["cat"] == cat_key and f["check"]]
            if filtered:
                result_html += f'<div class="cat-title">{cat_name}</div>'
                for f in filtered:
                    result_html += f'<div class="res-card">{f["text"]}</div>'

        if not result_html:
            result_html = "<p style='text-align:center; padding:20px;'>ယခုဇာတာအတွက် ထူးခြားသော နဒီယောဂများ မတွေ့ရှိသေးပါ။</p>"

        # ဂြိုဟ်ဒီဂရီများနှင့်အတူ အဟောပါဝင်သော HTML ကိုတစ်ပါတည်း ပို့ပေးခြင်း
        return jsonify({
            'positions': res,
            'result_html': result_html
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

app = app
