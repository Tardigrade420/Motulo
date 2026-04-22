import http.client
import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from dotenv import load_dotenv
load_dotenv()

#Global variables
jettys_file = Path("kaier.json")
token_dict = {}
ships_docked = {}
client_id = os.getenv('AIS_CLIENT_ID')
client_secret = os.getenv('AIS_CLIENT_SECRET')

#Funksjon for å hente token
def get_token(): 
    #Parametere til request
    global token_dict
    payload = urlencode({"scope": "ais", "grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret})
    
    #Sjekk om token er gyldig
    try:
        if datetime.now().timestamp() < token_dict.get("expires_at"):
            return token_dict.get("access_token")
    except:
        print("Feil med token. Henter ny token.")
    #Få ny token
    conn = None
    try:
        conn = http.client.HTTPSConnection("id.barentswatch.no")

        headers = {'Content-Type': "application/x-www-form-urlencoded"}

        conn.request("POST", "/connect/token", payload, headers)

        res = conn.getresponse()

        if res.status != 200:
            print(f"Request feilet: {res.status} {res.reason}")
            return None

        data = json.loads(res.read().decode("utf-8"))
        data["expires_at"] = datetime.now().timestamp() + data["expires_in"] - 60
        token_dict = data

        return data["access_token"]
    except:
        print("Kunne ikke hente token")
        return None
    finally:
        if conn is not None:
            conn.close()


#APT call til live ais
def api_call_ais(url, payload):
    token = get_token()
    
    if token is None:
        return None
    
    headers = {
        'Content-Type': "application/json",
        'Authorization': f"Bearer {token}",
        }
    
    conn = None
    try:
        conn = http.client.HTTPSConnection("live.ais.barentswatch.no")

        conn.request("POST", url, json.dumps(payload), headers)

        res = conn.getresponse()

        if res.status != 200:
            print(f"Request feilet: {res.status} {res.reason}")
            return None

        data = res.read().decode("utf-8")

        return json.loads(data)
    except:
        print("Kunne ikke hente båter")
        return None
    finally:
        if conn is not None:
            conn.close()
    

#Gå igjennom alle kaier og hent skip
def get_ships_docked():
    time_interval = datetime.now() - timedelta(seconds=60)
    jettys = json.loads(jettys_file.read_text())
    global ships_docked
    url = "/v1/latest/combined"
    
    #Oppdater kun hvis nødvendig
    if ships_docked.get("updated") and ships_docked.get("updated") > time_interval:
        return ships_docked
    else:
        print("Henter nye skip")
    
    for jetty in jettys:
        time = datetime.now(timezone.utc) - timedelta(minutes=60)
        payload = {
            "since": time.isoformat(),
            "modelType": "Simple",
            "geometry": jettys[jetty]
            }
        
        ships = api_call_ais(url, payload)
        if ships:
            ships_docked[jetty] = ships
        else:
            ships_docked[jetty] = []
    ships_docked["updated"] = datetime.now()
    
    return ships_docked