from flask import Flask, request, redirect
import os
import json

# Disable HDMI to save power
os.system('vcgencmd display_power 0')

app = Flask(__name__)

ALARM_FILE = '/home/cade/alarm_settings.json'

def load_alarm_settings():
    """Load alarm settings from file"""
    try:
        if os.path.exists(ALARM_FILE):
            with open(ALARM_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {'enabled': False, 'time': None}

def save_alarm_settings(settings):
    """Save alarm settings to file"""
    with open(ALARM_FILE, 'w') as f:
        json.dump(settings, f)

@app.route('/')
def index():
    with open('web_template.html', 'r') as f:
        html = f.read()

    settings = load_alarm_settings()
    alarm_time = settings.get('time')
    alarm_enabled = settings.get('enabled')

    alarm_color = '#007AFF' if (alarm_time and alarm_enabled) else 'rgba(255, 255, 255, 0.2)'
    alarm_display = alarm_time if alarm_time else 'Not Set'

    # Get default values for pickers
    default_hour = 7
    default_minute = 0
    if alarm_time:
        parts = alarm_time.replace(' AM', '').split(':')
        default_hour = int(parts[0])
        default_minute = int(parts[1])

    html = html.replace('{{ALARM_COLOR}}', alarm_color)
    html = html.replace('{{ALARM_DISPLAY}}', alarm_display)
    html = html.replace('{{DEFAULT_HOUR}}', str(default_hour))
    html = html.replace('{{DEFAULT_MINUTE}}', str(default_minute))

    return html

@app.route('/set_alarm', methods=['POST'])
def set_alarm():
    hour = request.form['hour']
    minute = request.form['minute']
    alarm_time = f"{hour.zfill(2)}:{minute.zfill(2)} AM"

    settings = {'enabled': True, 'time': alarm_time}
    save_alarm_settings(settings)

    return redirect('/')

@app.route('/disable_alarm', methods=['POST'])
def disable_alarm():
    settings = load_alarm_settings()
    settings['enabled'] = False
    # Keep the time, just disable it
    save_alarm_settings(settings)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)