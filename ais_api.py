import http.client
import json
import os
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from dotenv import load_dotenv
load_dotenv()

#Global variables
jettys_file = Path("kaier.json")
cor_file = Path("koordinater.json")
coordinates = json.loads(cor_file.read_text())
token_dict = {}
ships_docked = {}
kyst_token = None
client_id = os.getenv('AIS_CLIENT_ID')
client_secret = os.getenv('AIS_CLIENT_SECRET')
kyst_username = os.getenv('KYST_USERNAME')
kyst_password = os.getenv('KYST_PASSWORD')

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

#Funksjon for å hente token fra kyst
def get_token_kyst():
    payload = {"username": kyst_username, "password": kyst_password}
    headers = {'Content-Type': "application/json"}
    conn = None
    try:
        conn = http.client.HTTPSConnection("kystdatahuset.no")
        conn.request("POST", "/ws/api/auth/login", json.dumps(payload), headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        if data.get("success") == True:
            print('Token hentet fra kystdatahuset')
            return data.get("data").get("JWT")
        else:
            print(f"Feil med token: {data.get('errors')}")
            return None
    except Exception as e:
        print(f"Feil med token: {e}")
        return None
    finally:
        if conn is not None:
            conn.close()

#Funksjon for å gjøre en API call til kystdatahuset
def api_call_kyst(url):
    global kyst_token
    if kyst_token is None:
        kyst_token = get_token_kyst()
    if kyst_token is None:
        return None
    payload = ""
    headers = {
        'Content-Type': "application/json",
        'Authorization': f"Bearer {kyst_token}",
    }
    conn = None
    try:
        conn = http.client.HTTPSConnection("kystdatahuset.no")
        conn.request("GET", url, payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        if res.status == 401:
            kyst_token = get_token_kyst()
            if kyst_token is None:
                return None
            headers = {
                'Content-Type': "application/json",
                'Authorization': f"Bearer {kyst_token}",
            }
            conn.request("GET", url, headers)
            res = conn.getresponse()
            if res.status != 200:
                print(f"Feil med API call: {res.status} {res.reason}")
                return None
            data = json.loads(res.read().decode("utf-8"))
            return data
        elif res.status == 200:
            return data
        else:
            print(f"Feil med API call: {res.status} {res.reason}")
            return None
    except Exception as e:
        print(f"Feil med API call: {e}")
        print(headers)
        return None
    finally:
        if conn is not None:
            conn.close()

#Hente ais data via kallesignal
def get_position(callsign):
    call_url = f"/ws/api/ship/combined/callsign/{callsign}"
    ship_data = api_call_kyst(call_url)
    mmsi = None
    if ship_data:
        try:
            mmsi = ship_data.get("data")[0].get("mmsi")
        except:
            print("No mmsi found")
            return None
    if mmsi:
        url = "/v1/latest/combined"
        payload = {
            "mmsi": [mmsi]
        }
        ais_msg = api_call_ais(url, payload)
        if ais_msg:
            return ais_msg
        else:
            print("No ais message found")
            return None
    else:
        print("No mmsi found")
        return None
    
#Funksjon for å sjekke gjenværende distanse for skip
def get_distance(callsign, pos):
    if pos not in coordinates:
        print("Invalid position")
        return None
    ais = get_position(callsign)
    if ais:
        try:
            name = ais[0].get("name").title()
            ais_pos = (ais[0].get("latitude"), ais[0].get("longitude"))
            cog = ais[0].get("courseOverGround")
            sog = ais[0].get("speedOverGround")
            hdg = ais[0].get("trueHeading")
            msgtime = datetime.fromisoformat(ais[0].get("msgtime"))
        except:
            print(f"Failed to parse ais data: {Exception}")
            return None
        tgt_cog, dist = get_course_dist(ais_pos, coordinates[pos])
        if sog != 0:
            ttg = decimal_to_time(dist / sog)
        else:
            ttg = "N/A"
        if cog - tgt_cog > 180:
            diff_cog = cog - tgt_cog - 360
        elif cog - tgt_cog < -180:
            diff_cog = cog - tgt_cog + 360
        else:
            diff_cog = cog - tgt_cog
        age = datetime.now(timezone.utc) - msgtime
        minutes, seconds = divmod(age.total_seconds(), 60)
        age_str = f"{round(minutes)}min {round(seconds)}s"
        ship_data = {
            "name": name,
            "cog": round(cog),
            "sog": round(sog, 1),
            "hdg": round(hdg),
            "msgtime": msgtime,
            "tgt_cog": round(tgt_cog),
            "dist": round(dist, 1),
            "ttg": ttg,
            "diff_cog": round(diff_cog),
            "age": age_str
        }
        return ship_data
    else:
        print("No valid ais data found")
        return None

#Funksjon for å finne riktig kurs
def get_course_dist(pos1, pos2):
    lat1, lon1 = pos1
    lat2, lon2 = pos2

    # Konverter til radianer
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = phi2 - phi1
    delta_lon = math.radians(lon2 - lon1)

    # Korteste vei over 180°-meridianen
    if delta_lon > math.pi:
        delta_lon -= 2 * math.pi
    elif delta_lon < -math.pi:
        delta_lon += 2 * math.pi

    # Mercator latitude difference
    delta_psi = math.log(
        math.tan(math.pi / 4 + phi2 / 2)
        / math.tan(math.pi / 4 + phi1 / 2)
    )

    # Loksodromkurs
    course = math.degrees(math.atan2(delta_lon, delta_psi)) % 360

    # Faktor for øst/vest-komponenten
    if abs(delta_psi) > 1e-12:
        q = delta_phi / delta_psi
    else:
        q = math.cos(phi1)

    # Loksodromdistanse i radianer
    angular_distance = math.sqrt(
        delta_phi**2 + (q * delta_lon)**2
    )

    # 1 radian = 60 * 180/pi nautiske mil
    distance_nm = angular_distance * 60 * 180 / math.pi

    return course, distance_nm

#Funksjon for å konvertere desimal time til tid
def decimal_to_time(decimal_hours):
    total_minutes = round(decimal_hours * 60)
    hours, minutes = divmod(total_minutes, 60)

    return f"{hours:02d}:{minutes:02d}"

#API call til live ais
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