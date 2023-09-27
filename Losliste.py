import http.client
import sqlite3
import time
from bs4 import BeautifulSoup


#Hente data inn til database
def current_pilotages():
   conn = http.client.HTTPSConnection("www.shiprep.no")
   payload = "__VIEWSTATE=%2FwEPDwUKLTYwMjM1ODI1OWRkihciWXOT7la0fVxgo82dzspjLffjhsDX7ILdV%2Fpg4yc%3D&ctl00%24MainContent%24PilotageDispatchDepartmentDropDown=2353122&ctl00%24MainContent%24PilotageDipatchLocationDropDown=2353170&ctl00%24MainContent%24ShowPilotages=Show%2BPilotages"
   headers = {'Content-Type': "application/x-www-form-urlencoded" }
   conn.request("POST", "/shiprepwebui/currentpilotages.aspx", payload, headers)
   res = conn.getresponse()
   data = res.read()
   soup = BeautifulSoup(data, 'html.parser')
   #Organisere data
   head = []
   data = []
   i = 0
   for th in soup.find_all('th'):
      head.append('_' + str(i) + '_' + th.get_text())
      i += 1

   head_new = [item.replace('/', '_') for item in head]
   head_new = [item.replace(' ', '_') for item in head_new]
   head_str = ', '.join(head_new)

   #Slette gammel og opprette ny table
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
   return time.strftime("%H:%M")

def des_query(des):
   last_update = current_pilotages()
   con = sqlite3.connect('motulo.db')
   cur = con.cursor()
   col = "_0_ETA_ETD, _3_Ship_Name, _4_GT, _5_Type, _6_From, _7_To, _9_Locked"
   query = f'SELECT {col} FROM los WHERE (LOWER(_6_From) LIKE "{des}" OR LOWER(_7_To) LIKE "{des}" OR LOWER(_7_To) LIKE "sture" OR LOWER(_6_From) LIKE "sture") AND CAST(_4_GT AS INTEGER) >= 20000'
   cur.execute(query)
   res = cur.fetchall()
   cur.close()
   con.close()
   return res, last_update