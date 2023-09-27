import sqlite3
import pytz
import time
from datetime import datetime

# con = sqlite3.connect('test.db')
# cur = con.cursor()

# cur.execute('DROP TABLE IF EXISTS los;')

cest = datetime.now(tz=pytz.timezone('Europe/Oslo')).strftime('%H:%M:%S')
tm = cest.strftime('%H:%M:%S %z')

print(cest)