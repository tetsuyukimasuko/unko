from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from flask import Flask
from flask import request
from flask import make_response, jsonify
import os
import requests
import datetime
import pandas as pd

#import gspread
#from oauth2client.service_account import ServiceAccountCredentials
#from gspread_dataframe import get_as_dataframe

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/',methods=['GET'])
def index():
	return 'Hello World!'

@app.route('/event_search', methods=['POST'])
def event_search():

	req = request.get_json(silent=True, force=True)
	result = req.get("result")
	parameters = result.get("parameters")
	event_date = parameters.get("Event_date")
	place_query = parameters.get("Place")
	date_query = parameters.get("date")

	now = datetime.datetime.now()

	if event_date=='today':
		event_date = str(now.year) + "年" + str(now.month) + "月" + str(now.day) + "日"
		speak_date = "今日"
	elif event_date == 'tomorrow':
		event_date = str(now.year) + "年" + str(now.month) + "月" + str(now.day + 1) + "日"
		speak_date = "明日"
	elif event_date == '' :
		if date_query=='':
			event_date = str(now.year) + "年" + str(now.month) + "月" + str(now.day) + "日"
			speak_date = "今日"			
		else:
			dt_format = datetime.datetime.strptime(date_query,'%Y-%m-%d')
			event_date = str(dt_format.year) + "年" + str(dt_format.month) + "月" + str(dt_format.day) + "日"
			speak_date = str(dt_format.month) + "月" + str(dt_format.day) + "日"			

	scope = ['https://www.googleapis.com/auth/drive']

	#ダウンロードしたjsonファイルを同じフォルダに格納して指定する
	credentials = ServiceAccountCredentials.from_json_keyfile_name('EventScraper-d56f51f0aa3c.json', scope)
	gc = gspread.authorize(credentials)

	# # 共有設定したスプレッドシートの名前を指定する
	worksheet = gc.open("Event_Info").sheet1

	#dataframeにする
	df = get_as_dataframe(worksheet, parse_dates=False,index=None)


	#TODO ここから下はdataframeとして操作
	text = ""

	#event_dateしかなかった場合は、日付のみでフィルタリングする
	#または、All Areaでもこの条件を使う。
	if place_query == '' or place_query == 'All':
		df_filtered = df[df['日付'].isin([event_date])]
		length = len(df_filtered.index)

		#指定した日付のピタリ賞があった場合
		if length > 0:
			titles = df_filtered['イベント名'].values.tolist()
			places = df_filtered['場所'].values.tolist()
			timestamps = df_filtered['時間'].values.tolist()
			regions = df_filtered['地区'].values.tolist()
			text = speak_date + 'は、'

			for i in range(length):
				if i > 0:
					text = text + 'また、'
				if timestamps[i] == '-':
					text = text + places[i] + "で" + titles[i] + "があります。"
				else:
					text = text + places[i] + "で" + timestamps[i] + "から" + titles[i] + "があります。"
			text = text + 'お出かけしてみてはいかがでしょうか。'
		#なかった場合、一番近いものを持ってくる
		else:
			Founded = False
			date_list = df['日付'].values.tolist()
			dt_format_query = datetime.datetime.strptime(event_date,'%Y年%m月%d日')

			for j in range(1,len(date_list)):
				#datetimeに変換
				dt_format = datetime.datetime.strptime(date_list[j],'%Y年%m月%d日')
				if dt_format_query < dt_format:
					df_filtered = df[df['日付'].isin([date_list[j]])]
					Founded = True
					break
			if Founded:
				length = len(df_filtered.index)
				titles = df_filtered['イベント名'].values.tolist()
				places = df_filtered['場所'].values.tolist()
				timestamps = df_filtered['時間'].values.tolist()
				regions = df_filtered['地区'].values.tolist()
				text = speak_date + 'はイベントはありません。近い日にちだと、' + str(date_list[j]).replace('2018年','') + 'に'

				for i in range(length):
					if i > 0:
						text = text + 'また、'
					if timestamps[i] == '-':
						text = text + places[i] + "で" + titles[i] + "があります。"
					else:
						text = text + places[i] + "で" + timestamps[i] + "から" + titles[i] + "があります。"
				text = text + 'お出かけしてみてはいかがでしょうか。'
			else:
				text = 'すみません。あまり先の日程まではわかりません。'

	#地区の指定があった場合は地区でもフィルタリングする
	elif place_query != '':
		df_filtered = df[df['日付'].isin([event_date])]
		df_filtered = df_filtered[df_filtered['地区'].isin([place_query,'All Area'])]
		length = len(df_filtered.index)
		#指定した日付と地区のピタリ賞があった場合
		if length > 0:
			titles = df_filtered['イベント名'].values.tolist()
			places = df_filtered['場所'].values.tolist()
			timestamps = df_filtered['時間'].values.tolist()
			regions = df_filtered['地区'].values.tolist()
			text = speak_date + 'は、'

			for i in range(length):
				if i > 0:
					text = text + 'また、'
				if timestamps[i] == '-':
					text = text + places[i] + "で" + titles[i] + "があります。"
				else:
					text = text + places[i] + "で" + timestamps[i] + "から" + titles[i] + "があります。"

		#なかった場合、一番近いものを持ってくる
		else:
			df_filtered = df[df['地区'].isin([place_query])]
			date_list = df_filtered['日付'].values.tolist()
			dt_format_query = datetime.datetime.strptime(event_date,'%Y年%m月%d日')
			#listの長さがあった場合
			if len(date_list) > 0:
				Founded = False
				for j in range(1,len(date_list)):
					#datetimeに変換
					dt_format = datetime.datetime.strptime(date_list[j],'%Y年%m月%d日')

					if dt_format_query < dt_format:
						df_filtered = df_filtered[df_filtered['日付'].isin([date_list[j]])]
						Founded = True
						break
				if Founded:
					length = len(df_filtered.index)
					titles = df_filtered['イベント名'].values.tolist()
					places = df_filtered['場所'].values.tolist()
					timestamps = df_filtered['時間'].values.tolist()
					regions = df_filtered['地区'].values.tolist()
					text = '指定した地区ではイベントはありません。近い日にちだと、' + str(date_list[j]).replace('2018年','') + 'に'

					for i in range(length):
						if i > 0:
							text = text + 'また、'
						if timestamps[i] == '-':
							text = text + places[i] + "で" + titles[i] + "があります。"
						else:
							text = text + places[i] + "で" + timestamps[i] + "から" + titles[i] + "があります。"
				else:
					text = 'すみません。あまり先の日程まではわかりません。'
			#日付が見つからなかった場合
			else:
				text = 'しばらく、指定した地区ではイベントはありません。ホームページの更新をお待ちください。'

	#テキストを加工する。かっこが入っているものを消す
	try:
		text = text.replace('(いまいずみだい)','')
	except:
		pass
	try:
		text = text.replace('(おおひらやま)','')
	except:
		pass
	try:
		text = text.replace('町内会館','ちょーなぃかぃかん')
	except:
		pass

	r = make_response(jsonify({'speech':text,'displayText':text,'data':{'google':{'expect_user_response':False,'no_input_prompts':[],'is_ssml':False}}}))
	r.headers['Content-Type'] = 'application/json'

	return r


if __name__ == '__main__':
    app.run(debug=False, port=80, host='0.0.0.0')
