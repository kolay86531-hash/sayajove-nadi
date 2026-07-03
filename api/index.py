@app.route('/api/calc', methods=['GET'])
def calculate():
    try:
        dob = request.args.get('dob')
        tob = request.args.get('tob', '12:00')
        # ပုံမှန်အားဖြင့် dob မပါလာရင် Error မတက်အောင် စစ်ပေးပါ
        if not dob: return jsonify({'error': 'မွေးသက္ကရာဇ် လိုအပ်ပါသည်။'})
        
        # ... (ဂြိုဟ်တွက်ချက်မှု Logic အတိုင်းထားပါ) ...
        
        # transit_map မရှိရင်လည်း Error မတက်အောင် empty dict ပို့ပါ
        return jsonify({
            'html': html_content if html_content else "<p>အချက်အလက် မရှိပါ။</p>",
            'transit_map': transit_map if 'transit_map' in locals() else {},
            'chart_data': chart if 'chart' in locals() else {}
        })
    except Exception as e:
        return jsonify({'error': str(e), 'html': '', 'transit_map': {}, 'chart_data': {}})
fetch('/api/calc?dob=' + dob + '&tob=' + tob + '&city=' + city)
    .then(response => response.json())
    .then(data => {
        // [Safety Check] 1. Data ရှိမရှိ အရင်စစ်ပါ
        if (!data) {
            console.error("No data received");
            return;
        }

        // [Safety Check] 2. chart_data ရှိမှသာ ဇယားဆွဲပါ
        if (data.chart_data && typeof drawChart === "function") {
            drawChart(data.chart_data);
        }

        // [Safety Check] 3. transit_map ရှိမှသာ ကောဇာဂြိုဟ်တင်ပါ
        if (data.transit_map) {
            Object.keys(data.transit_map).forEach(house => {
                let el = document.getElementById('house-' + house);
                if (el) {
                    el.innerHTML += `<div style="color:red; font-size:10px;">${data.transit_map[house].join(', ')}</div>`;
                }
            });
        }

        // [Safety Check] 4. ဟောချက်ပြခြင်း
        if (data.html) {
            document.getElementById('result-div').innerHTML = data.html;
        } else if (data.error) {
            document.getElementById('result-div').innerHTML = `<p style="color:red;">${data.error}</p>`;
        }
    })
    .catch(err => {
        console.error("Fetch Error:", err);
        document.getElementById('result-div').innerHTML = "<p>Connection အဆင်မပြေပါ။</p>";
    });
