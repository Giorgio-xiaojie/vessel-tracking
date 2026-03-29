# vessel-tracking

## Description
The Vessel Tracking Dashboard is a dashboard and an AIS Vessel Mapping app.  The main landing page provides performance metrics, and the map will plot the position of each vessel in the AIS tracking system in real time.


## Background
This app was developed to monitor the health of the Raspberry Pi Zero and monitor the AIS service to ensure system up time.  


The map page provides a way to verify that data is in fact flowing as expected by plotting vessel locations in real time.


## Installation
```markdown
# Connect to your PI so that you can issue commands
SSH to Pi if using another device on your netowrk (like a PC) or remote into Pi and use local terminal

# Clone the repo (vessel-tracking directory will be created in the current directory the command is being ran from)
git clone git clone https://github.com/Giorgio-xiaojie/vessel-tracking
cd vessel-tracking

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn  (optional if running in production or as a service)

# Run it  (for dev purposes)
python app.py


# Run it as a service  (Alternatively)
Refer to documentation on systemd and services

# Access the Web Dashboard
In your browser http://<Your PI's IP>:8888

