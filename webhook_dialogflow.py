from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
import datetime

from flask import Flask
from flask import request
from flask import make_response, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
	req = request.get_json(silent=True, force=True)
	result = req.get("result")
	parameters = result.get("parameters")
	event_date = parameters.get("Event_date")
	now=datetime.datetime.now()

	if event_date=='today':
		event_date= str(now.year)+"年"+str(now.month)+"月"+str(now.day)+"日"
	elif event_date=='tomorrow':
		event_date= str(now.year)+"年"+str(now.month)+"月"+str(now.day+1)+"日"
	scope = ['https://www.googleapis.com/auth/drive']
    #ダウンロードしたjsonファイルを同じフォルダに格納して指定する
	credentials = ServiceAccountCredentials.from_json_keyfile_name('My First Project-fc3744a8d618.json', scope)
	gc = gspread.authorize(credentials)
    # # 共有設定したスプレッドシートの名前を指定する
	worksheet = gc.open("Event_Info").sheet1
	text=""
	cell = worksheet.findall(event_date)
	if len(cell) > 0:
		for cl in cell:
			if text!="":
				text += "また、"+str(worksheet.cell(cl.row,1).value) + "が" + str(worksheet.cell(cl.row,3).value)+"であります。"
			else:
				text = str(worksheet.cell(cl.row,1).value) + "が" + str(worksheet.cell(cl.row,3).value)+"であります。"

	else:
		text=event_date+'のイベントは見つかりませんでした。'
	
	r = make_response(jsonify({'speech':text,'displayText':text}))
	r.headers['Content-Type'] = 'application/json'
	
	return r

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')
