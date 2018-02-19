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
	place_query=parameters.get("Place")
	Event_Found=False
		
	now=datetime.datetime.now()

	if event_date=='today':
		event_date= str(now.year)+"年"+str(now.month)+"月"+str(now.day)+"日"
		speak_date="今日"
	elif event_date=='tomorrow':
		event_date= str(now.year)+"年"+str(now.month)+"月"+str(now.day+1)+"日"
		speak_date="明日"
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
			
			title=str(worksheet.cell(cl.row,1).value)
			place=str(worksheet.cell(cl.row,4).value)
			region=str(worksheet.cell(cl.row,10).value)
			timestamp=str(worksheet.cell(cl.row,3).value)
			
			if place_query==region:
				if timestamp=="-":
					tmp=place +"で"+title+"があります。"
				else:
					tmp=place +"で"+timestamp+"から"+title+"があります。"
				if text!="":
					text += "また、"+ tmp
				else:
					text = speak_date + "は、" +tmp
					
			elif place_query=='' or place_query=='All':
				if timestamp=="-":
					tmp=place +"で"+title+"があります。"
				else:
					tmp=place +"で"+timestamp+"から"+title+"があります。"
				if text!="":
					text += "また、"+ tmp
				else:
					text = speak_date + "は、" +tmp				
	if text=="":
		if place_query=='':
			text='その日はイベントはありません。'
		else:
			text='その日、指定した地区でのイベントはありません。'
		#TODO
		#一番近いイベントを一つ紹介する
		date_list=worksheet.col_values(2)
		for j in range(1,len(date_list)):
			#datetimeに変換
			dt_format=datetime.datetime.strptime(date_list[j],'%Y年%m月%d日')
			if now<dt_format:
				if place_query=='':
					Event_Found=True
					break
				else:
					if place_query==str(worksheet.cell(j,10).value):
						Event_Found=True
						break
		if Event_Found==False:
			text=text+'ホームページの更新をお待ちください。'
		else:
			title=str(worksheet.cell(j,1).value)
			place=str(worksheet.cell(j,4).value)
			region=str(worksheet.cell(j,10).value)
			timestamp=str(worksheet.cell(j,3).value)

			text= text+'近い日にちだと、'+str(dt_format.month)+"月"+str(dt_format.day)+"日に"

			if timestamp=="-":
				text=text+place +"で"+title+"があります。"
			else:
				text=text +place+"で"+timestamp+"から"+title+"があります。"
					
					
	#google_data={"expect_user_response": false,"no_input_prompts": [],"is_ssml": false}
	#json_data={"google": google_data}
	
	r = make_response(jsonify({'speech':text,'displayText':text,'data':{'google':{'expect_user_response':False,'no_input_prompts':[],'is_ssml':False}}}))
	r.headers['Content-Type'] = 'application/json'
	
	return r

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')
