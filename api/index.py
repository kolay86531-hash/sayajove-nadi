from flask import Flask, request, jsonify
import datetime
import math

app = Flask(__name__)

# =====================================================================
# 🌍 ၁။ မြန်မာနိုင်ငံရှိ မြို့ကြီးများ၏ တည်နေရာ (Coordinates) ဒေတာဘေ့စ်
# =====================================================================
CITY_DB = {
    # ရန်ကုန်တိုင်း
    "ရန်ကုန်": {"lat": 16.8409, "lon": 96.1735},
    "သန်လျင်": {"lat": 16.7583, "lon": 96.2500},
    "မှော်ဘီ": {"lat": 17.1167, "lon": 96.0333},
    
    # မန္တလေးတိုင်း
    "မန္တလေး": {"lat": 21.9588, "lon": 96.0891},
    "ပြင်ဦးလွင်": {"lat": 22.0392, "lon": 96.4647},
    "မိတ္ထီလာ": {"lat": 20.8833, "lon": 95.8667},
    "မြင်းခြံ": {"lat": 21.5833, "lon": 95.3833},
    "ညောင်ဦး": {"lat": 21.2000, "lon": 94.9167},
    "ပုဂံ": {"lat": 21.1667, "lon": 94.8667},
    
    # နေပြည်တော်
    "နေပြည်တော်": {"lat": 19.7633, "lon": 96.0785},
    
    # ရှမ်းပြည်နယ်
    "တောင်ကြီး": {"lat": 20.7888, "lon": 97.0333},
    "လားရှိုး": {"lat": 22.9333, "lon": 97.7500},
    "ကျိုင်းတုံ": {"lat": 21.2833, "lon": 99.6000},
    "ကလော": {"lat": 20.6333, "lon": 96.5667},
    "တာချီလိတ်": {"lat": 20.4552, "lon": 99.8821},
    
    # တနင်္သာရီတိုင်း
    "မြိတ်": {"lat": 12.4333, "lon": 98.6167},
    "ထားဝယ်": {"lat": 14.0833, "lon": 98.2000},
    "ကော့သောင်း": {"lat": 9.9833, "lon": 98.5500},
    
    # ဧရာဝတီတိုင်း
    "ပုသိမ်": {"lat": 16.7833, "lon": 94.7333},
    "ဟင်္သာတ": {"lat": 17.6500, "lon": 95.3667},
    "မြောင်းမြ": {"lat": 16.6000, "lon": 94.9333},
    
    # ပဲခူးတိုင်း
    "ပဲခူး": {"lat": 17.3333, "lon": 96.4833},
    "ပြည်": {"lat": 18.8167, "lon": 95.2167},
    "တောင်ငူ": {"lat": 18.9333, "lon": 96.4333},
    
    # စစ်ကိုင်းတိုင်း
    "မုံရွာ": {"lat": 22.1167, "lon": 95.1333},
    "စစ်ကိုင်း": {"lat": 21.8783, "lon": 95.9792},
    "ရွှေဘို": {"lat": 22.5667, "lon": 95.7000},
    "ကလေး": {"lat": 23.2000, "lon": 94.0500},
    
    # မကွေးတိုင်း
    "မကွေး": {"lat": 20.1500, "lon": 94.9333},
    "ပခုက္ကူ": {"lat": 21.3333, "lon": 95.0833},
    
    # မွန်ပြည်နယ်
    "မော်လမြိုင်": {"lat": 16.4905, "lon": 97.6282},
    "သထုံ": {"lat": 16.9167, "lon": 97.3667},
    
    # ကရင်ပြည်နယ် / ကယားပြည်နယ်
    "ဘားအံ": {"lat": 16.8903, "lon": 97.6342},
    "လွိုင်ကော်": {"lat": 19.6742, "lon": 97.2094},
    
    # ရခိုင်ပြည်နယ် / ချင်းပြည်နယ်
    "စစ်တွေ": {"lat": 20.1436, "lon": 92.8958},
    "သံတွဲ": {"lat": 18.4667, "lon": 94.3667},
    "ဟားခါး": {"lat": 22.6425, "lon": 93.6019},
    
    # ကချင်ပြည်နယ်
    "မြစ်ကြီးနား": {"lat": 25.3833, "lon": 97.4000},
    "ဗန်းမော်": {"lat": 24.2500, "lon": 97.2333}
}

# 🏠 မူလအိမ်ပိုင်ရှင်များ စာရင်း
OWNERS = {
    'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
    'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
}

@app.route('/api/calc', methods=['GET'])
def calculate():
    dob_str = request.args.get('dob', '1985-11-08')
    tob_str = request.args.get('tob', '15:03')
    city_input = request.args.get('city', '').strip()

    # --- 🌍 မြို့ရှာဖွေခြင်းစနစ် Logic ---
    if city_input in CITY_DB:
        lat = CITY_DB[city_input]["lat"]
        lon = CITY_DB[city_input]["lon"]
        current_city = city_input
    else:
        # ကျောင်းသားရိုက်သောမြို့ မတွေ့ပါက Default အနေဖြင့် ရန်ကုန်ကို သတ်မှတ်ပေးခြင်း
        lat = 16.8409
        lon = 96.1735
        current_city = "ရန်ကုန် (Default)"

    try:
        # 🗓️ ဒိုင်ယာရီရက်စွဲ ပိုင်းဖြတ်ခြင်း
        y, m, d = map(int, dob_str.split('-'))
        h, mn = map(int, tob_str.split(':'))
        
        # ⚠️ မှတ်ချက်- ဤနေရာတွင် ဆရာ့ဆာဗာရှိ Ephemeris သို့မဟုတ် တကယ့်နက္ခတ်တွက်ချက်မှုစနစ်ကို ချိတ်ဆက်ရပါမည်။
        # ဥပမာအဖြစ် ပုံသေနမူနာ Positions ဒေတာကို ထည့်သွင်းပြသထားပါသည်။
        mock_positions = {
            'Ascendant': 35.5, 'Sun': 212.4, 'Moon': 148.1, 'Mars': 195.3,
            'Mercury': 225.8, 'Jupiter': 312.0, 'Venus': 185.2, 'Saturn': 238.9,
            'Rahu': 42.1, 'Ketu': 222.1
        }
        
        pos = mock_positions

        # 🔮 ဇာတာတည်ဆောက်ခြင်းဆော့ဝဲလ် Logic
        chart = {}
        for p, deg in pos.items():
            chart[p] = {
                "house": math.floor(deg / 30),
                "degree": deg % 30
            }

        # =====================================================================
        # 📐 နဒီတွက်ချက်မှုဆိုင်ရာ သင်္ချာ Functions များ
        # =====================================================================
        def is_aspect(p1, p2):
            if p1 not in chart or p2 not in chart: return False
            diff = (chart[p2]["house"] - chart[p1]["house"] + 12) % 12
            # 1, 5, 9, 3, 7, 11 ဆက်သွယ်ချက်များ (နဒီအမြင် သီအိုရီအရ)
            return diff in [0, 4, 8, 2, 6, 10]

        def is_interchange(p1, p2):
            if p1 not in chart or p2 not in chart: return False
            h1 = chart[p1]["house"]
            h2 = chart[p2]["house"]
            return (h1 in OWNERS.get(p2, [])) and (h2 in OWNERS.get(p1, []))

        def get_dist_from_jupiter(planet):
            if 'Jupiter' not in chart or planet not in chart: return 0
            return (chart[planet]["house"] - chart['Jupiter']["house"] + 12) % 12 + 1

        def is_shakata_pos():
            if 'Jupiter' not in chart or 'Moon' not in chart: return False
            dist = (chart['Moon']["house"] - chart['Jupiter']["house"] + 12) % 12 + 1
            return dist in [6, 8]

        def is_kala_sarpa_yoga():
            if 'Rahu' not in chart or 'Ketu' not in chart: return False
            r_pos = chart['Rahu']["house"]
            k_pos = chart['Ketu']["house"]
            planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
            count_cw = 0
            for p in planets:
                if p in chart:
                    h = chart[p]["house"]
                    if (r_pos < k_pos and r_pos < h < k_pos) or (r_pos > k_pos and (h > r_pos or h < k_pos)):
                        count_cw += 1
            return count_cw == 7 or (len(planets) - count_cw) == 7

        # =====================================================================
        # 📜 ၂။ နဒီအဟောကျမ်း ဒေတာဘေ့စ် (ဆရာစိတ်ကြိုက် ထပ်တိုးနိုင်သည့် နေရာ)
        # =====================================================================
        effects = [
            # ကံကြမ္မာကဏ္ဍ (fortune)
            {"cat": "fortune", "check": is_aspect('Jupiter', 'Venus') and is_aspect('Jupiter', 'Mercury'), "text": "<b>ဓနသိဒ္ဓိယောဂ</b> ငွေကြေးကံ အလွန်ကောင်းမွန်ပြီး ပညာရှိများ၏ အကူအညီ ရရှိမည်။"},
            {"cat": "fortune", "check": is_aspect('Sun', 'Jupiter'), "text": "<b>တနင်္ဂနွေ+ကြာသပတေး</b> အစိုးရ သို့မဟုတ် အကြီးအကဲများ၏ အထောက်အပံ့ ရရှိမည်။"},
            {"cat": "fortune", "check": is_aspect('Jupiter', 'Venus'), "text": "<b>ကြာသပတေး+သောကြာ</b> ကြီးပွားချမ်းသာမည့် ဇာတာရှင်ဖြစ်သည်။ အိမ်၊ ခြံ၊ မြေ ကံကောင်းတတ်သည်။"},
            {"cat": "fortune", "check": is_aspect('Jupiter', 'Moon'), "text": "<b>ကြာသပတေး+တနင်္လာ</b> စိတ်သဘောထား နူးညံ့ပြီး ခရီးသွားခြင်းဖြင့် ကံကောင်းတတ်သည်။"},
            {"cat": "fortune", "check": is_aspect('Mercury', 'Venus'), "text": "<b>ဗုဒ္ဓဟူး+သောကြာ</b> ပညာဉာဏ် ထက်မြက်ပြီး စီးပွားရေးတွင် အောင်မြင်မည်။"},
            {"cat": "fortune", "check": is_aspect('Sun', 'Mercury'), "text": "<b>တနင်္ဂနွေ+ဗုဒ္ဓဟူး (ဗုဓာဒိစ္စယောဂ)</b> ဉာဏ်ပညာ ထက်မြက်ပြီး စာပေပညာ၊ ကုန်သွယ်မှုတို့ဖြင့် ကျော်ကြားတတ်သည်။"},
            {"cat": "fortune", "check": is_shakata_pos(), "text": "<b>သကပ်ယုဂ် (Shakata Yoga)</b> ဘဝသည် တက်လိုက်၊ ကျလိုက်နှင့် လှည်းဘီးကဲ့သို့ အလှည့်အပြောင်း ကြုံရတတ်သည်။"},
            {"cat": "fortune", "check": is_kala_sarpa_yoga(), "text": "<b>ကာလသရ္ပယုဂ် (Kala Sarpa Yoga)</b> ဘဝတွင် အတိုက်အခံများ ကြုံရတတ်သော်လည်း ဘဝဒုတိယပိုင်းတွင် အံ့ဩဖွယ်ရာ အောင်မြင်မှု ရတတ်သည်။"},

            # အလုပ်အကိုင်ကဏ္ဍ (career)
            {"cat": "career", "check": is_aspect('Saturn', 'Ketu'), "text": "<b>စနေ+ကိတ်</b> အလုပ်အကိုင်တွင် ရုတ်တရက် အပြောင်းအလဲများ သို့မဟုတ် ဝိညာဉ်ရေးရာနှင့် ပတ်သက်သော အလုပ်များ အကျိုးပေးမည်။"},
            {"cat": "career", "check": is_interchange('Mars', 'Mercury'), "text": "<b>အင်္ဂါ+ဗုဒ္ဓဟူး (အိမ်ဖလှယ်ခြင်း)</b> စကားပြောဆိုရာတွင် အလွန်ထက်မြက်ပြီး နည်းပညာ သို့မဟုတ် စီးပွားရေးဖြင့် အောင်မြင်မည်။"},
            {"cat": "career", "check": is_aspect('Saturn', 'Jupiter'), "text": "<b>စနေ+ကြာသပတေး</b> အလုပ်အကိုင်တွင် ဆရာတစ်ဆူ ဖြစ်တတ်သည်။ တာဝန်ကြီးသော ရာထူးများ ရရှိမည်။"},
            {"cat": "career", "check": is_aspect('Saturn', 'Mercury'), "text": "<b>စနေ+ဗုဒ္ဓဟူး</b> စာရင်းအင်း၊ စာရေးစာချီ သို့မဟုတ် ကုန်သွယ်မှုလုပ်ငန်းများဖြင့် တည်ငြိမ်အောင်မြင်မည်။"},

            # အိမ်ထောင်ရေးကဏ္ဍ (marriage)
            {"cat": "marriage", "check": is_aspect('Venus', 'Ketu'), "text": "<b>သောကြာ+ကိတ်</b> အမျိုးသားဇာတာရှင်အတွက် အိမ်ထောင်ဖက်မှာ ဘာသာတရား ကိုင်းရှိုင်းသူ ဖြစ်တတ်သည်။ ဇနီးသည်နှင့် ဆက်ဆံရေး အေးစက်တတ်သည်။"},
            {"cat": "marriage", "check": is_aspect('Venus', 'Mars'), "text": "<b>သောကြာ+အင်္ဂါ</b> အိမ်ထောင်ဖက်နှင့် စိတ်ဆန္ဒ အလွန်ကိုက်ညီတတ်ပြီး အချစ်ရေး၊ အိမ်ထောင်ရေး သံယောဇဉ် အားကောင်းသည်။"},

            # မိသားစုကဏ္ဍ (family)
            {"cat": "family", "check": is_aspect('Moon', 'Rahu'), "text": "<b>တနင်္လာ+ရာဟု</b> မိခင်ဖြစ်သူမှာ ဇာတာရှင်မွေးစတွင် ကျန်းမာရေး အားနည်းတတ်ခြင်း သို့မဟုတ် စိတ်သောက ရောက်တတ်သည်။"},
            {"cat": "family", "check": is_aspect('Sun', 'Saturn'), "text": "<b>တနင်္ဂနွေ+စနေ</b> ဖခင်နှင့် အမြင်မတူဘဲ စိတ်သဘောထား ကွဲလွဲတတ်ခြင်း၊ သို့မဟုတ် ဖခင်ကျန်းမာရေး ဂရုစိုက်ရတတ်သည်။"},

            # ဝိညာဉ်ရေးရာကဏ္ဍ (spiritual)
            {"cat": "spiritual", "check": is_aspect('Jupiter', 'Ketu'), "text": "<b>ကြာသပတေး+ကိတ်</b> တရားထူး၊ တရားမြတ်များ ရရှိတတ်သည်။ လောကုတ္တရာ ပညာတွင် အလွန်ထူးချွန်မည်။"},
            {"cat": "spiritual", "check": is_aspect('Mercury', 'Ketu'), "text": "<b>ဗုဒ္ဓဟူး+ကိတ်</b> ဗေဒင်၊ နက္ခတ် သို့မဟုတ် လျှို့ဝှက်ဆန်းကြယ်သော ပညာရပ်များကို အလိုလို သိမြင်တတ်သော ဉာဏ်ရှိသည်။"},
            {"cat": "spiritual", "check": is_aspect('Moon', 'Ketu'), "text": "<b>တနင်္လာ+ကိတ်</b> စိတ်အာရုံ ထူးခြားဆန်းပြားခြင်း၊ အိပ်မက်မှန်ခြင်းနှင့် နာမ်ပိုင်းဆိုင်ရာကို ဝါသနာပါခြင်း။"},
            {"cat": "spiritual", "check": get_dist_from_jupiter('Ketu') == 12, "text": "<b>မုတ္တိယုဂ် (Moksha Yoga)</b> ကိတ်သည် ကြာသပတေးမှ ရေတွက်သော် ၁၂ တန့်တွင် ရှိသဖြင့် ဝိညာဉ်ရေးရာနှင့် လွတ်မြောက်ရာလမ်းကို ရှာဖွေမည့်သူ ဖြစ်သည်။"}
        ]

        # =====================================================================
        # 🎨 HTML Formatting ဖြင့် Frontend သို့ ပြန်လည်ပို့ဆောင်ခြင်း
        # =====================================================================
        cat_names = {
            "fortune": "🔮 ကံကြမ္မာ",
            "career": "💼 အလုပ်အကိုင်",
            "marriage": "💍 အိမ်ထောင်ရေး",
            "family": "🏡 မိသားစုရေးရာ",
            "spiritual": "🧘 ဝိညာဉ်ရေးရာနှင့် ပညာရပ်"
        }

        result_html = f"<div style='margin-bottom: 10px; color: #555; font-size:13px;'>📍 တွက်ချက်ပေးသောမြို့ - <b>{current_city}</b> (Lat: {lat}, Lon: {lon})</div>"
        
        has_yoga = False
        for cat, cat_title in cat_names.items():
            # သက်ဆိုင်ရာ ကဏ္ဍအလိုက် စည်းမျဉ်းကိုက်ညီသော အဟောများကို စစ်ထုတ်ခြင်း
            filtered_effects = [e for e in effects if e["cat"] == cat and e["check"]]
            
            if filtered_effects:
                has_yoga = True
                result_html += f"<div class='cat-title'>{cat_title}</div>"
                for f in filtered_effects:
                    result_html += f"<div class='res-card'>{f['text']}</div>"

        if not has_yoga:
            result_html += "<p style='text-align:center; padding:20px;'>ယခုဇာတာအတွက် ထူးခြားသော နဒီယောဂများ မတွေ့ရှိသေးပါ။</p>"

        return jsonify({
            "positions": pos,
            "result_html": result_html
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
