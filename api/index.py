from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime, timedelta

app = Flask(__name__)

# Lahiri Ayanamsa စနစ်
swe.set_sid_mode(swe.SIDM_LAHIRI)

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

        # ဂြိုဟ်တွက်ချက်ခြင်း (Natal & Transit)
        planets = {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS, 'Mercury': swe.MERCURY, 
                   'Jupiter': swe.JUPITER, 'Venus': swe.VENUS, 'Saturn': swe.SATURN}
        
        res, chart = {}, {}
        transit_map = {i: [] for i in range(12)} # 0-11 အိမ်ကွက်များအတွက်
        
        for name, p_id in planets.items():
            # Natal Position
            pos = swe.calc_ut(jd_ut, p_id, swe.FLG_SIDEREAL)[0][0]
            res[name] = round(pos, 2)
            house = int(pos // 30)
            chart[name] = {'house': house}
            
            # Transit Position (လက်ရှိအချိန် ကောဇာဂြိုဟ်)
            t_pos = swe.calc_ut(swe.julday(datetime.now().year, datetime.now().month, datetime.now().day), p_id, swe.FLG_SIDEREAL)[0][0]
            t_house = int(t_pos // 30)
            transit_map[t_house].append(name[:3]) # ဂြိုဟ်နာမည် အတိုကောက်

        # Helper Functions
        def is_aspect(p1, p2):
            diff = (chart[p2]['house'] - chart[p1]['house'] + 12) % 12
            return diff in [0, 4, 8, 2, 6, 10]

        # Dasha Logic
        moon_lon = res['Moon']
        nak_index = int(moon_lon / (360 / 27))
        dasha_order = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
        current_dasha = dasha_order[nak_index % 9]

        # Effects List
        effects = [
            {"cat": "dasha", "check": True, "text": f"<b>လက်ရှိဂြိုဟ်သက်:</b> {current_dasha} သက်ဝင်နေပါသည်။"},
            {"cat": "fortune", "check": is_aspect('Jupiter', 'Venus'), "text": "<b>ဓနသိဒ္ဓိယောဂ:</b> ငွေကြေးဓန ပေါများမည်။"}
        ]

        # HTML ထုတ်ခြင်း
        html_content = f"<div>📍 တွက်ချက်မှု: {city_input}</div>"
        for cat in ["dasha", "fortune", "career"]:
            items = [e['text'] for e in effects if e['cat'] == cat and e.get('check')]
            if items:
                html_content += f"<h3>{cat.capitalize()}</h3>" + "".join([f"<p>{i}</p>" for i in items])

        # Backend ကနေ ဇယားအတွက် အချက်အလက် အပြည့်အစုံ ပို့ပေးလိုက်ပါပြီ
        return jsonify({
            'html': html_content,
            'transit_map': transit_map, # Frontend မှာ ဇယားကွက်ပေါ် တင်ပြဖို့
            'chart_data': chart
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
