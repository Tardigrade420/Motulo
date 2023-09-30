import http.client
import sqlite3
from datetime import datetime
import time
import pytz
from bs4 import BeautifulSoup
import schedule
import threading


last_update = None
fedje_id = 2353170
#Hente data inn til database
def current_pilotages():
   try:
      conn = http.client.HTTPSConnection("www.shiprep.no")
      payload = "__VIEWSTATE=%2FwEPDwUKLTYwMjM1ODI1OWRkihciWXOT7la0fVxgo82dzspjLffjhsDX7ILdV%2Fpg4yc%3D&ctl00%24MainContent%24PilotageDispatchDepartmentDropDown=2353122&ctl00%24MainContent%24PilotageDipatchLocationDropDown=None&ctl00%24MainContent%24ShowPilotages=Show%2BPilotages"
      headers = {'Content-Type': "application/x-www-form-urlencoded" }
      conn.request("POST", "/shiprepwebui/currentpilotages.aspx", payload, headers)
      res = conn.getresponse()
      data = res.read()
      soup = BeautifulSoup(data, 'html.parser')
   except Exception as exception:
      error = type(exception)
      return("Shiprep req failed: " + str(error) + " " + str(exception))
   head = []
   data = []
   i = 0
   #Slette gammel og opprette ny table
   try:
      for th in soup.find_all('th'):
         head.append(th.get_text())
         if th.get_text() == '':
            head[i] = str(i+1)
         i += 1
      head_str = '"' + '", "'.join(head) + '"'
      con = sqlite3.connect('motulo.db')
      cur = con.cursor()
      cur.execute('DROP TABLE IF EXISTS los;')
      cur.execute(f'CREATE TABLE IF NOT EXISTS los ({head_str});')
      for tr in soup.find_all('tr'):
         data.clear()
         for td in tr.find_all('td'):
            data.append(td.get_text(strip = True))
            if len(data) < 10:
               continue
            cur.execute('INSERT INTO los VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
      con.commit()
      cur.close()
      con.close()
      global last_update
      cest = datetime.now(tz=pytz.timezone('Europe/Oslo'))
      last_update = cest.strftime("%H:%M:%S")
   except Exception as exception:
      error = type(exception)
      last_update = ("Database write failure: " + str(error) + " " + str(exception))
   

def worker():
   schedule.every(15).seconds.do(current_pilotages)
   while True:
      schedule.run_pending()
      time.sleep(1)

def start():
   current_pilotages()
   loop_thread = threading.Thread(target=worker)
   loop_thread.start()
   

def des_query(des):
   try:
      con = sqlite3.connect('motulo.db')
      cur = con.cursor()
      col = '"ETA/ETD", "Ship Name", "GT", "Type", "From", "To", "Locked"'
      query = f'SELECT {col} FROM los WHERE (LOWER("From") LIKE "{des}" OR LOWER("To") LIKE "{des}" OR LOWER("To") LIKE "sture" OR LOWER("From") LIKE "sture") AND CAST("GT" AS INTEGER) >= 20000'
      cur.execute(query)
      res = cur.fetchall()
      cur.close()
      con.close()
      return res, last_update
   except Exception as exception:
      error = type(exception)
      return("Database query failure: " + str(error) + " " + str(exception))
