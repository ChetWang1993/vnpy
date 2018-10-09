import pandas as pd
import sys
from datetime import datetime

filename = sys.argv[1]

res = pd.read_csv(filename)

#res['Date'] = [datetime.strptime(x.split(' ')[0], '%Y/%m/%d').strftime('%Y-%m-%d') for x in res['datetime']]
res['Date'] = [x.split(' ')[0] for x in res['datetime']]
#res['Time'] = [datetime.strptime(x.split(' ')[1], '%H:%M').strftime('%H:%M:00') for x in res['datetime']]
res['Time'] = [x.split(' ')[1] for x in res['datetime']]
res['High'] = res['high']
res['Low'] = res['low']
res['Open'] = res['open']
res['Close'] = res['close']
res['TotalVolume'] = [int(x*100) for x in res['volume']]

res.to_csv(filename, index = False)