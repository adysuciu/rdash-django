DASHBOARD_STATS = [
    {"label": "Users", "value": "80", "tone": "green", "icon": "people"},
    {"label": "Servers", "value": "16", "tone": "red", "icon": "server"},
    {"label": "Documents", "value": "225", "tone": "amber", "icon": "files"},
    {"label": "Tickets", "value": "62", "tone": "blue", "icon": "lifebuoy"},
]

SERVER_ROWS = [
    {"name": "RDVMPC001", "address": "238.103.133.37", "status": "online"},
    {"name": "RDVMPC002", "address": "68.66.63.170", "status": "online"},
    {"name": "RDVMPC003", "address": "76.117.212.33", "status": "down"},
    {"name": "RDPHPC001", "address": "91.88.224.5", "status": "online"},
    {"name": "RDESX001", "address": "197.188.15.93", "status": "online"},
    {"name": "RDESX003", "address": "209.25.191.61", "status": "down"},
    {"name": "RDTerminal02", "address": "136.80.122.212", "status": "degraded"},
]

USER_ROWS = [
    {"id": 1, "name": "Joe Bloggs", "role": "Super Admin", "account": "AZ23045"},
    {"id": 2, "name": "Timothy Hernandez", "role": "Admin", "account": "AU24783"},
    {"id": 3, "name": "Joe Bickham", "role": "User", "account": "AM23781"},
]

ACTIVITY_ITEMS = [
    "Dashboard shell rebuilt on Django 6",
    "Static assets now served by WhiteNoise",
    "Container health check available at /healthz/",
]
