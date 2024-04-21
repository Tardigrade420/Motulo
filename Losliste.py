import http.client
import sqlite3
from datetime import datetime
import time
import pytz
from bs4 import BeautifulSoup
import schedule
import threading

errormsg = ""
last_update = None
lock = threading.Lock()

#Hente inn alle losoppdrag fra kvitsøy los og lagre i sqlite database
def current_pilotages():
   payload = "__EVENTTARGET%3D&=__EVENTARGUMENT%3D&=ctl00%24HiddenMap%24hfSelectedLocationID%3D&__VIEWSTATE=%2FwEPDwUKLTYwMjM1ODI1OWRkOBAwahtW5IAitaKOvDd7zJyluXZpmWg8eUb5Yx51ZDU%3D&__VIEWSTATEGENERATOR=272EAD92&ctl00%24MainContent%24PilotageDispatchDepartmentDropDown=2353122&ctl00%24MainContent%24PilotageDipatchLocationDropDown=None&ctl00%24MainContent%24ShowPilotages=Show%2BPilotages"
   headers = {'Content-Type': "application/x-www-form-urlencoded" }
   cest = datetime.now(tz=pytz.timezone('Europe/Oslo'))
   head = []
   list_data = []
   i = 0
   global last_update
   global errormsg
   try:
      #Hente data inn til database
      conn = http.client.HTTPSConnection("www.shiprep.no")
      conn.request("POST", "/shiprepwebui/currentpilotages.aspx", payload, headers)
      res = conn.getresponse()
      data = res.read()
      soup = BeautifulSoup(data, 'html.parser')
      
      with lock:
         for th in soup.find_all('th'):
            head.append(th.get_text())
            if th.get_text() == '':
               head[i] = str(i+1)
            i += 1
         if len(head) < 1:
            raise Exception("Empty response")
         head_str = '"' + '", "'.join(head) + '"'
         con = sqlite3.connect('motulo.db')
         cur = con.cursor()
         cur.execute('DROP TABLE IF EXISTS los;')
         cur.execute(f'CREATE TABLE IF NOT EXISTS los ({head_str});')
         
         for tr in soup.find_all('tr'):
            list_data.clear()
            for td in tr.find_all('td'):
               list_data.append(td.get_text(strip = True))
               if len(list_data) < 10:
                  continue
               cur.execute('INSERT INTO los VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', list_data)
         con.commit()
         cur.close()
         con.close()
         errormsg = ""
         last_update = cest.strftime("%H:%M:%S")
   except Exception as exception:
      error = type(exception)
      errormsg = "Feilet kl: " + cest.strftime("%H:%M:%S, ") + str(error) + str(exception)

#Sørge for oppdatering av database hvert minutt
def worker():
   schedule.every(147).seconds.do(current_pilotages)
   while True:
      schedule.run_pending()
      time.sleep(1)

#Sørge for at oppdatering av database ikke forstyrrer lasting av webside
def start():
   current_pilotages()
   loop_thread = threading.Thread(target=worker)
   loop_thread.start()
   
#generell sql query til database
def des_query(ton, des):
    global errormsg
    if len(des) == 0:
       des_q = ''
    elif type(des) == tuple and len(des) > 1:
       des_q = f'(LOWER("From") IN {des} OR LOWER("To") IN {des}) AND'
    elif type(des) == tuple and len(des) == 1:
       des_q = f'(LOWER("From") LIKE "{des[0]}" OR LOWER("To") LIKE "{des[0]}") AND'
    elif type(des) == str:
        des_q = f'(LOWER("From") LIKE "{des}" OR LOWER("To") LIKE "{des}") AND'
    try:
       con = sqlite3.connect('motulo.db')
       cur = con.cursor()
       col = '"ETA/ETD", "Ship Name", "GT", "Type", "From", "To", "Locked"'
       query = f'''SELECT {col} FROM los WHERE {des_q} CAST("GT" AS INTEGER) >= {ton}'''
       cur.execute(query)
       res = cur.fetchall()
       cur.close()
       con.close()
       return res, last_update, errormsg
    except Exception as exception:
       error = type(exception)
       errormsg = "Database query failure: " + str(error) + " " + str(exception)
       res = ["feil"]
       return res, last_update, errormsg

#Spesifikk sql query til database for Kårstø
def karsto_query(des):
    global errormsg
    des_l = ["karsto"]
    for i in des:
       des_l.append(i)
    des_t = tuple(des_l)
    if len(des) == 0:
       des_q = 'OR LOWER("To") LIKE "karsto"'
    elif type(des) == tuple and len(des) >= 1:
       des_q = f'OR LOWER("To") IN {des_t}'
    elif type(des) == str:
        des_q = f'OR LOWER("To") LIKE "{des}"'
    try:
       con = sqlite3.connect('motulo.db')
       cur = con.cursor()
       col = '"ETA/ETD", "Ship Name", "GT", "Type", "From", "To", "Locked"'
       query = f'''SELECT {col} FROM los WHERE LOWER("From") LIKE "karsto" {des_q}'''
       cur.execute(query)
       res = cur.fetchall()
       cur.close()
       con.close()
       return res, last_update, errormsg
    except Exception as exception:
       error = type(exception)
       #errormsg = f'Feil {des_q}, {des}'
       errormsg = "Database query failure: " + str(error) + " " + str(exception)
       res = ["feil"]
       return res, last_update, errormsg