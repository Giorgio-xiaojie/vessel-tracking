from flask import Flask, render_template
import psutil
import os
import time
import subprocess
import re


MAX_CPU_TEMP=70
MAX_CPU_USAGE=80


def signal_level(dbm):
    if dbm >= -50:
        return 4
    elif dbm >= -60:
        return 3
    elif dbm >= -70:
        return 2
    elif dbm >= -80:
        return 1
    else:
        return 0

def get_ais_status():
    # 检测你的AIS程序是否在运行
    for p in psutil.process_iter(['name']):
        if 'ais_script_name' in p.info['name']:
            return "Running"
    return "Stopped"

start = time.time()

app = Flask(__name__)

@app.route("/")
def home(): 
    wifi = subprocess.getoutput("iwconfig wlan0 | grep 'Signal level'")
    quality = int(re.search(r'Link Quality=(\d+)', wifi).group(1))
    max_quality = int(re.search(r'Link Quality=\d+/(\d+)', wifi).group(1))
    signal_dbm = signal_level(int(re.search(r'Signal level=(-?\d+)', wifi).group(1)))
    img_name = "images/wifi/" + str(signal_dbm) + ".jpeg"
    quality_percent = (quality * 100 // max_quality)
    end = int(time.time())
    tm = int((end-start))
    m = round((tm)//(60),0)
    h = round((m)//(60),0)
    d = round((h)//(24),0)
    cpu_usage = psutil.cpu_percent(interval=1)
    flag=get_ais_status()

    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0
    except:
        temp = 9999  # artificially high value when temperature unavailable
    
    temp_color= "blue" if temp < MAX_CPU_TEMP else "red"
    cpu_color= "blue" if cpu_usage < MAX_CPU_USAGE else "red"
    wifi_color= "green" if quality_percent > 60 else "orange"
   
    return render_template('index.html',
                           temp=temp,
                           wifi=wifi,
                           quality_percent=quality_percent,
                           m=m,
                           h=h,
                           d=d,
                           cpu_usage=cpu_usage,
                           temp_color=temp_color,
                           cpu_color=cpu_color,
                           wifi_color=wifi_color,
                           flag=flag,
                           img_name=img_name)

@app.route("/page1")
def page1():
    return """
    <div style="text-align:center;">
    <a href="https://aisstream.io/documentation" target="_blank">
        <button style="font-size:30px;padding:0px 0px;">
        AIS API Documentation
        </button>
    </a>
    </div>
    """
    
if __name__=="__main__":
    app.run(debug=True,host="0.0.0.0",port=8888)


#       <p style="text-align:center;color:black;font-size:15px">
#       PiAware Version:
#       </p>
#
#       <p style="text-align:center;color:black;font-size:15px">
#       Dump1090-fa Version:
#       </p>
#
#       <p style="text-align:center;color:black;font-size:15px">
#       Dump978-fa Version:
#       </p>
#memory = psutil.virtual_memory()
#disk = psutil.disk_usage('/')
#print(f"--- 树莓派状态 ---")
#print(f"CPU 使用率: {cpu_usage}%")
#print(f"CPU 温度: {temp}°C")
#print(f"内存使用: {memory.percent}% (剩余 {memory.available // 1024 // 1024}MB)")
#print(f"磁盘使用: {disk.percent}%")
#time = psutil.boot_time()    
#signal_gs = (signal_dbm + 1) * "█" + (5 - signal_dbm - 1) * "[]"