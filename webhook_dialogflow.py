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
	text =event_date
	r = make_response(jsonify({'speech':text,'displayText':text}))
	r.headers['Content-Type'] = 'application/json'
	return r

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')
