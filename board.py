from flask import Flask, request, Response, session
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_very_strong_secret_key_here'

# 简单的行为追踪（生产环境应使用数据库）
attacker_profiles = {}

def create_attacker_profile():
    profile = {
        'user_agent': request.headers.get('User-Agent'),
        'languages': request.headers.get('Accept-Language'),
        'first_seen': datetime.now(),
        'ip_history': set()
    }
    return profile

@app.before_request
def track_attacker():
    # 创建基于浏览器指纹的ID
    fp_id = hashlib.md5(
        f"{request.headers.get('User-Agent')}:{request.headers.get('Accept-Language')}".encode()
    ).hexdigest()
    
    if fp_id not in attacker_profiles:
        attacker_profiles[fp_id] = create_attacker_profile()
    
    # 记录IP变化
    attacker_profiles[fp_id]['ip_history'].add(request.remote_addr)
    
    # 存储到session中用于显示警告
    if len(attacker_profiles[fp_id]['ip_history']) > 1:
        session['multi_ip_warning'] = True

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    ip_warning = ""
    if session.get('multi_ip_warning'):
        ip_warning = """
        <div style="border: 3px solid red; padding: 10px; margin: 20px 0;">
            <h2 style="color: red;">⚠️ WE'VE DETECTED YOUR IP SWITCHING ⚠️</h2>
            <p>We know you're the same person using different IP addresses</p>
            <p>Your attack pattern has been recorded</p>
        </div>
        """
    
    return Response(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SECURITY ALERT</title>
        <style>
            body {{ 
                background-color: black; 
                color: white; 
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
            }}
            .warning {{ color: red; font-weight: bold; }}
            .ip-box {{
                background: #222;
                padding: 10px;
                margin: 20px auto;
                width: 50%;
                border: 1px solid red;
            }}
            .blink {{ animation: blink 1s step-end infinite; }}
            @keyframes blink {{ 50% {{ opacity: 0; }} }}
        </style>
    </head>
    <body>
        <h1 class="warning">SECURITY ALERT</h1>
        <h2>UNAUTHORIZED ACCESS DETECTED</h2>
        
        {ip_warning}
        
        <div class="ip-box">
            <p>Your current IP: <span class="warning">{request.remote_addr}</span></p>
            <p>Timestamp: {datetime.now()}</p>
        </div>
        
        <p class="blink warning">STOP ATTACKING THIS WEBSITE</p>
        
        <p>All your activities are being logged and analyzed</p>
        <p>Legal action may be taken against continued attacks</p>
    </body>
    </html>
    """, status=403, mimetype='text/html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
