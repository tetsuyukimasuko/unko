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

#Add
#from cek_sdk import RequestHandler
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import pandas as pd
from gspread_dataframe import get_as_dataframe

# Flask app should start in global layout
app = Flask(__name__)

pref_ids = {
      "01" : "北海道",
      "02" : "青森県",
      "03" : "岩手県",
      "04" : "宮城県",
      "05" : "秋田県",
      "06" : "山形県",
      "07" : "福島県",
      "08" : "茨城県",
      "09" : "栃木県",
      "10" : "群馬県",
      "11" : "埼玉県",
      "12" : "千葉県",
      "13" : "東京都",
      "14" : "神奈川県",
      "15" : "新潟県",
      "16" : "富山県",
      "17" : "石川県",
      "18" : "福井県",
      "19" : "山梨県",
      "20" : "長野県",
      "21" : "岐阜県",
      "22" : "静岡県",
      "23" : "愛知県",
      "24" : "三重県",
      "25" : "滋賀県",
      "26" : "京都府",
      "27" : "大阪府",
      "28" : "兵庫県",
      "29" : "奈良県",
      "30" : "和歌山県",
      "31" : "鳥取県",
      "32" : "島根県",
      "33" : "岡山県",
      "34" : "広島県",
      "35" : "山口県",
      "36" : "徳島県",
      "37" : "香川県",
      "38" : "愛媛県",
      "39" : "高知県",
      "40" : "福岡県",
      "41" : "佐賀県",
      "42" : "長崎県",
      "43" : "熊本県",
      "44" : "大分県",
      "45" : "宮崎県",
      "46" : "鹿児島県",
      "47" : "沖縄県"
    }

def ResponseForLaunchRequest():
    result = {
                "version": "0.1.0",
                "sessionAttributes": {},
                "response": {
                    "outputSpeech": {
                        "type": "SpeechList",
                        "values": [{
                            "type": "PlainText",
                            "lang": "ja",
                            "value": "わかりました。ラジオ体操を流します。"
                            },
                            {
                            "type": "URL",
                            "lang": "" ,
                            "value": "https://change-jp.box.com/shared/static/uiyqhfkdap37z3ocowey07lpfa4sq86b.mp3"
                            }]
                        },
                    "card": {},
                    "directives": [],
                    "shouldEndSession": True
                    }
                }

    return result

@app.route('/', methods=['GET'])
def root():
    return 'Hello World!'


def TextToResponse(text,end_session=False):

    result = {
                "version": "0.1.0",
                "sessionAttributes": {},
                "response": {
                    "outputSpeech": {
                        "type": "SimpleSpeech",
                        "values": 
                            {
                            "type": "PlainText",
                            "lang": "ja",
                            "value": text
                            }
                        },
                    "card": {},
                    "directives": [],
                    "shouldEndSession": end_session
                    }
                }
    return result

def PriceSearch(pref_name,city_name):

    pref_ids_inv = {v:k for k, v in pref_ids.items()}
    pref_id = pref_ids_inv[pref_name]

    url = 'https://opendata.resas-portal.go.jp/api/v1/cities?prefCode=' + pref_id
    headers = {'X-API-KEY': 'PPZDakUYlOkv8uVtQwX0uAs6B6qOoCtiHihBREs0'}
    r = requests.get(url,headers=headers).json()
    print(r)
    r = r['result']

    for data in r:
        name = data['cityName']
        city_id = data['cityCode']
        if name == city_name:
            break
    else:
        return 0

    url = 'https://opendata.resas-portal.go.jp/api/v1/townPlanning/estateTransaction/bar?year=2015&cityCode={0}&displayType=1&prefCode={1}'.format(city_id,str(int(pref_id)))
    headers = {'X-API-KEY': 'PPZDakUYlOkv8uVtQwX0uAs6B6qOoCtiHihBREs0'}
    r = requests.get(url,headers=headers).json()
    r = r['result']

    price = r['years'][0]['value']

    return price
    

def AverageSearch(pref_name):

    pref_ids_inv = {v:k for k, v in pref_ids.items()}
    pref_id = pref_ids_inv[pref_name]

    url = 'https://opendata.resas-portal.go.jp/api/v1/townPlanning/estateTransaction/bar?year=2015&cityCode=-&displayType=1&prefCode=' + str(int(pref_id))
    headers = {'X-API-KEY': 'PPZDakUYlOkv8uVtQwX0uAs6B6qOoCtiHihBREs0'}
    r = requests.get(url,headers=headers).json()
    r = r['result']

    price = r['years'][0]['value']

    return price

@app.route('/price_search', methods=['POST'])
def price_search():

    #ここから追加
    try:
        rh = RequestHandler('com.change-jp.search_price')
        request_body = request.data
        request_header = request.headers
        rh._verify_request(request_body,request_header)
    except:
        return make_response('Invalid signature.')



    #ここまで追加




    #json解析
    req = request.get_json(silent=True, force=True)
    req = req.get('request')
    type = req.get('type')
    intent = req.get('intent')
    slots = intent.get('slots')

    if type == 'LaunchRequest':
        result = TextToResponse('不動産取引価格を調べます。都道府県と市区町村名を言ってください。')
    elif type == 'IntentRequest':
        #都道府県
        try:
            pref = slots['Prefecture']['value']
        except:
            pref = ''

        #市区町村
        try:
            city_or_area = slots['City']['value']
        except:
            try:
                city_or_area = slots['Area']['value']
            except:
                city_or_area = ''

        #市区町村名だけの場合、絞り込むように促す
        if pref == '':
            result = TextToResponse('都道府県と市区町村名の両方が必要です。')
        #都道府県名だけの場合、最大値と最小値を返す。
        elif city_or_area == '':
            price = AverageSearch(pref)
            text = '2015年の{0}における平均地価は{1}円です。'.format(pref,price)
            result = TextToResponse(text)
        else:
            price = PriceSearch(pref,city_or_area)
            
            if price > 0:
                text = '2015年の{0}における地価は{1}円です。'.format(city_or_area,price)
                result = TextToResponse(text)
            else:
                text = '{0}は{1}の市区町村ではありません。'.format(city_or_area,pref)
                result = TextToResponse(text)
    elif type == 'SessionEndedRequest':
        text = '私もシロガネーゼになりたいです。'
        result = TextToResponse(text,end_session=True)

    #Clovaに返す
    print(result)    
    r = make_response(jsonify(result))
    r.headers['Content-Type'] = 'application/json'
    
    return r

@app.route('/',methods=['GET'])
def index():
    return 'Hello World!'

@app.route('/radio_exercise', methods=['POST'])
def radio_exercise():

    #json解析
    req = request.get_json(silent=True, force=True)
    type = req.get('request')
    type = type.get('type')

    if type == 'LaunchRequest':
        result = ResponseForLaunchRequest()
    else:
        pass

    #Clovaに返す
    r = make_response(jsonify(result))
    r.headers['Content-Type'] = 'application/json'
    
    return r


@app.route('/event_search', methods=['POST'])
def event_search():
	req = request.get_json(silent=True, force=True)
	result = req.get("result")
	parameters = result.get("parameters")
	event_date = parameters.get("Event_date")
	place_query = parameters.get("Place")
	date_query = parameters.get("date")

	now = datetime.datetime.now()

	if event_date == 'today':
		event_date = str(now.year) + "年" + str(now.month) + "月" + str(now.day) + "日"
		speak_date = "今日"
	elif event_date == 'tomorrow':
		event_date = str(now.year) + "年" + str(now.month) + "月" + str(now.day + 1) + "日"
		speak_date = "明日"
	elif event_date == '' :
		if date_query == '':
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

