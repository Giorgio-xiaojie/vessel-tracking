from datetime import datetime
from flask import Flask, render_template
import psutil
import time
import subprocess
import re


MAX_CPU_TEMP = 70
MAX_CPU_USAGE = 80


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
    for p in psutil.process_iter(["name"]):
        if p.info["name"] and "ais_script_name" in p.info["name"]:
            return "Running"
    return "Stopped"


def get_wifi_metrics():
    wifi = subprocess.getoutput("iwconfig wlan0 | grep 'Signal level'")
    quality_match = re.search(r"Link Quality=(\d+)/(\d+)", wifi)
    signal_match = re.search(r"Signal level=(-?\d+)", wifi)

    if not quality_match or not signal_match:
        return {
            "quality_percent": None,
            "signal_bars": 0,
            "signal_dbm": None,
            "img_name": "images/wifi/0.jpeg",
            "status_text": "Unavailable",
            "status_color": "status-unknown",
        }

    quality = int(quality_match.group(1))
    max_quality = int(quality_match.group(2))
    signal_dbm = int(signal_match.group(1))
    signal_bars = signal_level(signal_dbm)
    quality_percent = quality * 100 // max_quality

    if quality_percent > 60:
        status_color = "status-good"
        status_text = "Stable"
    elif quality_percent > 35:
        status_color = "status-warn"
        status_text = "Fair"
    else:
        status_color = "status-bad"
        status_text = "Weak"

    return {
        "quality_percent": quality_percent,
        "signal_bars": signal_bars,
        "signal_dbm": signal_dbm,
        "img_name": f"images/wifi/{signal_bars}.jpeg",
        "status_text": status_text,
        "status_color": status_color,
    }


def get_uptime_parts():
    uptime_seconds = max(int(time.time() - psutil.boot_time()), 0)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    return days, hours, minutes


def get_status_class(is_healthy):
    return "status-good" if is_healthy else "status-warn"


def build_stream_snapshot(pi_status, ais_status):
    is_running = ais_status == "Running"
    freshness_seconds = 18 if is_running else 94
    upload_size_kb = 142 if is_running else 0
    records_per_batch = 100 if is_running else 0
    uploads_per_min = 12 if is_running else 0
    messages_per_min = 124 if is_running else 0
    buffer_depth = 3 if is_running else 27
    lag_seconds = 4 if is_running else 42

    return {
        "title": "AIS vessel stream",
        "overall_label": "healthy" if is_running else "degraded",
        "overall_class": "status-good" if is_running else "status-warn",
        "metrics": [
            {
                "label": "last upload size",
                "value": f"{upload_size_kb} KB",
                "detail": "vessels_PNW.json",
            },
            {
                "label": "last upload",
                "value": f"{freshness_seconds}s ago",
                "detail": datetime.utcnow().strftime("%H:%M:%S UTC"),
            },
            {
                "label": "records",
                "value": str(records_per_batch),
                "detail": "per batch",
            },
        ],
        "checks": [
            {
                "label": "system service",
                "value": "active (running)" if is_running else "restarting",
                "class": "status-good" if is_running else "status-warn",
            },
            {
                "label": "blob freshness",
                "value": "within threshold" if is_running else "monitoring gap",
                "class": "status-good" if is_running else "status-warn",
            },
            {
                "label": "blob size",
                "value": "normal" if is_running else "below expected",
                "class": "status-good" if is_running else "status-warn",
            },
            {
                "label": "flow rate",
                "value": f"{messages_per_min} msg/min in, {uploads_per_min} uploads/min out",
                "class": "status-good" if is_running else "status-warn",
            },
        ],
        "footer_left": "refreshes every 30s",
        "footer_right": "pi2 / cruciblestorage",
        "flow_stats": [
            {"label": "messages/min", "value": messages_per_min},
            {"label": "uploads/min", "value": uploads_per_min},
            {"label": "buffer depth", "value": buffer_depth},
            {"label": "lag", "value": f"{lag_seconds}s"},
        ],
        "pi_status": pi_status,
    }

app = Flask(__name__)


@app.route("/")
def home():
    wifi_metrics = get_wifi_metrics()
    days, hours, minutes = get_uptime_parts()
    cpu_usage = psutil.cpu_percent(interval=1)
    ais_status = get_ais_status()

    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0
    except OSError:
        temp = None

    pi_status = {
        "temp": round(temp, 1) if temp is not None else "N/A",
        "cpu_usage": round(cpu_usage, 1),
        "uptime": f"{days}d {hours}h {minutes}m",
        "wifi_percent": wifi_metrics["quality_percent"],
        "wifi_text": wifi_metrics["status_text"],
        "wifi_status_class": wifi_metrics["status_color"],
        "temp_status_class": get_status_class(temp is not None and temp < MAX_CPU_TEMP),
        "cpu_status_class": get_status_class(cpu_usage < MAX_CPU_USAGE),
        "ais_status": ais_status,
        "ais_status_class": "status-good" if ais_status == "Running" else "status-warn",
        "img_name": wifi_metrics["img_name"],
        "signal_dbm": wifi_metrics["signal_dbm"],
    }

    summary_cards = [
        {
            "title": "Pi health",
            "value": f"{pi_status['cpu_usage']}% CPU",
            "detail": f"{pi_status['temp']} C / {pi_status['uptime']}",
            "status": "stable" if cpu_usage < MAX_CPU_USAGE else "warm",
            "class": pi_status["cpu_status_class"],
        },
        {
            "title": "Wi-Fi link",
            "value": (
                f"{pi_status['wifi_percent']}%"
                if pi_status["wifi_percent"] is not None
                else "Unavailable"
            ),
            "detail": pi_status["wifi_text"],
            "status": pi_status["wifi_text"].lower(),
            "class": pi_status["wifi_status_class"],
        },
        {
            "title": "AIS service",
            "value": ais_status,
            "detail": "local vessel feed process",
            "status": ais_status.lower(),
            "class": pi_status["ais_status_class"],
        },
        {
            "title": "Flow health",
            "value": "Healthy" if ais_status == "Running" else "Needs attention",
            "detail": "frontend mock until backend telemetry is added",
            "status": "pipeline view",
            "class": "status-good" if ais_status == "Running" else "status-warn",
        },
    ]

    return render_template(
        "index.html",
        generated_at=datetime.now().strftime("%I:%M %p"),
        summary_cards=summary_cards,
        stream_snapshot=build_stream_snapshot(pi_status, ais_status),
        pi_status=pi_status,
    )

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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8888)
