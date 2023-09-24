import http.client
import sqlite3
from bs4 import BeautifulSoup

def test():
   return head_str

#Hente data
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

def gt_query(gt):
   con = sqlite3.connect('motulo.db')
   cur = con.cursor()
   query = f'SELECT * FROM los WHERE CAST(_4_GT AS INTEGER) >= {gt}'
   cur.execute(query)
   res = cur.fetchall()
   cur.close()
   con.close()
   return res

def des_query(des):
   con = sqlite3.connect('motulo.db')
   cur = con.cursor()
   col = "_0_ETA_ETD, _3_Ship_Name, _4_GT, _5_Type, _6_From, _7_To, _9_Locked"
   query = f'SELECT {col} FROM los WHERE (LOWER(_6_From) LIKE "{des}" OR LOWER(_7_To) LIKE "{des}") AND CAST(_4_GT AS INTEGER) >= 20000'
   cur.execute(query)
   res = cur.fetchall()
   cur.close()
   con.close()
   return res

# result = des_query("mongstad")
# print(result)
# for row in result:
#     ship = row[3]
#     eta = row[0]
#     ton = row[4]
#     loc = row[9]

#     # Process the data as needed
#     print(ship, eta, ton, loc)