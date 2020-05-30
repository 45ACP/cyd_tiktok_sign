
from flask import Flask, jsonify, request
#from main import start_hook
import frida,sys,os,time,random,requests,hashlib,json,eventlet
from urllib.parse import quote

# ======================== Inject start ========================


def on_detached(reason, crash):
    print("on_detached()")
    print("\treason:", reason)
    print("\tcrash:", crash)
	
def on_process_crashed(crash):
    print("on_process_crashed")
    print("\tcrash:", crash)
	
def is_frida_running():
	cmdReturn = os.popen('adb shell "ps|grep frida-server"').read()
	if "root" in cmdReturn:
		return True
	return False

def inject():
	os.system('adb version')
	cmdReturn = os.popen('adb connect 127.0.0.1:7555').read()
	if "connected" in cmdReturn:
		os.system('adb forward tcp:27042 tcp:27042')
		os.system('adb forward tcp:27043 tcp:27043')
		print("[*] Mapping port 27042-27043 successful.")
		os.system('adb shell "chmod 777 /data/local/tmp/frida-server"')
		print("[*] Grant frida-server 777.")
		if is_frida_running():
			print("[*] frida-server already running...")
		else:
			print("[*] Starting frida-server...")
			os.system('adb shell "/data/local/tmp/frida-server -D"')
	else:
		print("[*] Device not connected!")

	# time.sleep(2)
	print("[*] get_remote_device()...")
	# device = frida.get_usb_device(timeout=5)
	device = frida.get_remote_device()
	app_package_name = "com.ss.android.ugc.aweme"
	print("[*] Patching "+app_package_name+"...")
	pid = device.spawn([app_package_name])
	device.resume(pid)
	time.sleep(1)

	device.on('process-crashed', on_process_crashed)

	session = device.attach(pid)
	print("[*] start hook")

	session.on('detached', on_detached)

	# 加载脚本
	with open("douyin_lite.js", "r", encoding="utf-8") as file:
		js_code = file.read()
	script = session.create_script(js_code)
	#script.on('message', on_message)
	print("[*] load start")
	script.load()
	print("[*] load end")
	return script

script = inject()
# ======================== Inject end ========================



app = Flask(__name__)

@app.route("/")
def index():
	return "/Bridge Services running..."

@app.route("/restart")
def restart():
	global script
	script = inject()
	return jsonify({
		"code": 1,
		"message": "Restart operation was successful"
	})

@app.route("/bridge/")
def bridge():
	action = request.args.get("action")
	t = time.time()
	p_timestamp_ms = str(round(t * 1000))
	p_timestamp = str(round(t))
	
	if action == "search":
		word = request.args.get("word")
		cursor = request.args.get("cursor")
		count = request.args.get("count")
		word = quote(word)
		current_timestamp = str(int(time.time() * 1000))
		url = "https://aweme-hl.snssdk.com/aweme/v1/discover/search/?cursor=" + cursor + "&keyword=" + word + "&count=" + count + "&type=1&ts=" + current_timestamp[:-3] + "&app_type=lite&os_api=23&device_type=MI%205sw&device_platform=android&ssmix=a&iid=100170432800&manifest_version_code=284&dpi=270&uuid=510000000007925&version_code=284&app_name=douyin_lite&cdid=08b3a0e3-e6a5-4754-b7e8-1514e8250974&version_name=2.8.4&openudid=96c7594f73116e20&device_id=70501033524&resolution=810*1440&os_version=6.0.1&language=zh&device_brand=Xiaomi&ac=wifi&update_version_code=2840&aid=2329&channel=baidu&_rticket=" + current_timestamp + "&as=a111111111111111111111&cp=a000000000000000000000&mas"
		args = script.exports.getsign(url,json.dumps([]))
		x_gorgon = args.get("X-Gorgon")
		x_khronos = args.get("X-Khronos")

		response = requests.get(
			url=url,
			headers={
				"Host": "aweme-hl.snssdk.com",
				"Connection": "keep-alive",
				"Cookie": "odin_tt=a900e5fd7ce1f4c2d49de90e1fb9af468bb3ae1fad94d142d34f42e0087338cfd7fe03b0080a5242e17d62769239142d",
				"Accept-Encoding": "gzip",
				"X-SS-REQ-TICKET": x_khronos + str(random.randint(125, 896)),
				"X-SS-TC": "0",
				"X-SS-RS": "0",
				"User-Agent": "com.ss.android.ugc.aweme.lite/242 (Linux; U; Android 6.0; zh_CN; HTC M8w; Build/MRA58K; Cronet/58.0.2991.0)",
				"X-Khronos": x_khronos,
				"X-Gorgon": x_gorgon,
			}
		)
		# print("===================================")
		# print(response.json())
		user_list = response.json().get("user_list")
		if user_list is None or user_list == []:
			users = []
			# print(response.json())
		else:
			users = list()
			for user in user_list:
				current_user = user.get("user_info")
				tmp_d = dict()
				tmp_d["uid"] = current_user.get("uid")
				tmp_d["short_id"] = current_user.get("short_id")
				tmp_d["nickname"] = current_user.get("nickname")
				tmp_d["gender"] = current_user.get("gender")
				tmp_d["signature"] = current_user.get("signature")
				tmp_d["avatar_uri"] = current_user.get("avatar_uri")
				tmp_d["birthday"] = current_user.get("birthday")
				tmp_d["is_verified"] = current_user.get("is_verified")
				tmp_d["following_count"] = current_user.get("following_count")
				tmp_d["follower_count"] = current_user.get("follower_count")
				tmp_d["favoriting_count"] = current_user.get("favoriting_count")
				tmp_d["total_favorited"] = current_user.get("total_favorited")
				tmp_d["unique_id"] = current_user.get("unique_id")
				tmp_d["region"] = current_user.get("region")
				tmp_d["unique_id_modify_time"] = current_user.get("unique_id_modify_time")
				tmp_d["share_qrcode_uri"] = current_user.get("share_qrcode_uri")
				tmp_d["sec_uid"] = current_user.get("sec_uid")
				tmp_d["language"] = current_user.get("language")
				tmp_d["constellation"] = current_user.get("constellation")
				users.append(tmp_d)

		print(json.dumps(response.json(), indent=4, ensure_ascii=False))
		return jsonify({
			"code": 0,
			"x_g": x_gorgon,
			"x_k": x_khronos,
			"data": users,
			"message": "success"
		})
	# 抖加投放
	elif action == "douplus_create":
		amemv_id = request.args.get("amemv_id")
		sessionid = request.args.get("sessionid")
		
		if amemv_id == "" or sessionid == "" or amemv_id is None or sessionid is None:
			return jsonify({"success": "false","message": "Invalid params"})

		useragent = "com.ss.android.ugc.aweme/100001 (Linux; U; Android 6.0.1; zh_CN; SM-G9200; Build/MMB29K; Cronet/TTNetVersion:79d23018 2020-02-03 QuicVersion:ac58aac6 2020-01-20)"
		request_url = "https://aweme-hl.snssdk.com/aweme/v2/douplus/order/create/?item_id="+amemv_id+"&budget=50&budget_int=50000&charge=50&charge_int=50000&coupon_discount_amount=0&gender=0&source=order_list&from_recommend=0&pay_type=1&delivery_type=1&aim=44&fans_budget=0&duration=6&target_conversion_bid=0&schema=1&coupon_bonus_amount=0&is_vcd=1&request_tag_from=h5&os_api=23&device_type=SM-G9200&device_platform=android&ssmix=a&iid=105838812475&callback_url=https%3A%2F%2Faweme.snssdk.com%2Ffalcon%2Fdouyin_falcon%2Fdou_plus%2Forder_status%2F%3Fforce_close%3D1%26item_id%3D"+amemv_id+"%26hide_status_bar%3D0%26hide_nav_bar%3D1%26status_bar_style_type%3D0%26status_bar_color%3Dffffff%26status_font_dark%3D1%26loading_bgcolor%3Dffffff"
		# 测试添加
		request_url += '&manifest_version_code=100001&dpi=640&uuid=359600061455733&version_code=100000&app_name=aweme&cdid=8c5a3efa-1f80-4531-a683-c4049a320720' # 通过
		request_url += '&version_name=10.0.0&ts='+p_timestamp+'&openudid=a77045a6cf16a82b&device_id=60897362918&resolution=1440*2560&os_version=6.0.1&language=zh' # 通过
		request_url += '&device_brand=samsung&app_type=normal&ac=wifi&update_version_code=10009900&channel=baidu&aid=1128&_rticket='+p_timestamp_ms #去除aid后通过测试

		args = script.exports.getsign(request_url,json.dumps([]))
		x_gorgon = args.get("X-Gorgon")
		x_khronos = args.get("X-Khronos")

		response = requests.get(
			url=request_url,
			headers={
				"Host": "api3-normal-c-hl.amemv.com",
				"Connection": "keep-alive",
				"User-Agent": useragent,
				"Accept-Encoding": "gzip, deflate",
				"Cookie": "sessionid="+sessionid+";",
				"X-Khronos": x_khronos,
				"X-Gorgon": x_gorgon
			}
		)
		return jsonify(response.json());
	# 抖加明细
	elif action == "douplus_detail":
		task_id = request.args.get("task_id")
		if task_id == "" or task_id is None:
			return jsonify({"success": "false","message": "Invalid params"})

		cookie = "msh=TjBTTzUQ5p1CQ8ZPaNgPQwH040g; sid_guard=bfc2d5c6fcc89665f919e90a57104334%7C1581672153%7C5184000%7CTue%2C+14-Apr-2020+09%3A22%3A33+GMT; uid_tt=04f0801635c409ce9c5180daf9175606; uid_tt_ss=04f0801635c409ce9c5180daf9175606; sid_tt=bfc2d5c6fcc89665f919e90a57104334; sessionid=bfc2d5c6fcc89665f919e90a57104334; sessionid_ss=bfc2d5c6fcc89665f919e90a57104334"
		request_url = "https://aweme-lq.snssdk.com/aweme/v2/douplus/ad/?task_id="+task_id+"&request_tag_from=h5&os_api=23&device_type=MI%205s&device_platform=android&ssmix=a&iid=103543330186&manifest_version_code=981&dpi=270&uuid=990000000161275&version_code=981&app_name=aweme&cdid=8f3db477-2377-4d6b-a99b-29063844099e&version_name=9.8.1&ts=1582696572&openudid=ce7aea385bc7015b&device_id=69705133757&resolution=810*1440&os_version=6.0.1&language=zh&device_brand=Xiaomi&app_type=normal&ac=wifi&update_version_code=9802&aid=1128&channel=tengxun_new&_rticket=1582696411448"

		args = script.exports.getsign(request_url,[])

		x_gorgon = args.get("X-Gorgon")
		x_khronos = args.get("X-Khronos")

		response = requests.get(
			url=request_url,
			headers={
				"Host": "api3-normal-c-hl.amemv.com",
				"User-Agent": "Aweme 9.7.1 rv:97103 (iPhone; iPhone OS 9.1; zh_CN) Cronet",
				"Cookie": cookie,
				"X-Khronos": x_khronos,
				"X-Gorgon": x_gorgon
			}
		)
		return jsonify(response.json());
	# 视频评论获取
	elif action == "comment":
		amemv_id = request.args.get("amemv_id")
		sessionid = request.args.get("sessionid")

		if amemv_id == "" or sessionid == "" or amemv_id is None or sessionid is None:
			return jsonify({"success": "false","message": "Invalid params"})

		request_url = "https://api3-normal-c-hl.amemv.com/aweme/v2/comment/list/?aweme_id="+amemv_id+"&cursor=0&count=20&address_book_access=1&gps_access=1&forward_page_type=1&os_api=23&device_type=OPPO%20R9s&ssmix=a&manifest_version_code=920&dpi=480&uuid=A0000061464D5B&app_name=aweme&version_name=9.2.0&ts="+p_timestamp+"&app_type=normal&ac=wifi&update_version_code=9202&channel=douyin_tengxun_wzl&_rticket="+p_timestamp_ms+"&device_platform=android&iid=97479104960&version_code=920&cdid=ed51d374-2f28-4465-9ab1-392643e0b8d3&openudid=98000d3887d9772b&device_id=36905115566&resolution=1080*1920&os_version=6.0.1&language=zh&device_brand=OPPO&aid=1128&mcc_mnc=46001"

		args = script.exports.getsign(request_url,json.dumps([]))
		x_gorgon = args.get("X-Gorgon")
		x_khronos = args.get("X-Khronos")

		response = requests.get(
			url=request_url,
			headers={
				"Host": "api3-normal-c-hl.amemv.com",
				"Connection": "keep-alive",
				"User-Agent": "com.ss.android.ugc.aweme/100001 (Linux; U; Android 6.0.1; zh_CN; SM-G9200; Build/MMB29K; Cronet/TTNetVersion:79d23018 2020-02-03 QuicVersion:ac58aac6 2020-01-20)",
				"Accept-Encoding": "gzip, deflate",
				"Cookie": "sessionid="+sessionid+";",
				"X-Khronos": x_khronos,
				"X-Gorgon": x_gorgon
			}
		)
		return jsonify(response.json());
	# elif action == "getvideo":

	# 	cookie = "msh=TjBTTzUQ5p1CQ8ZPaNgPQwH040g; sid_guard=bfc2d5c6fcc89665f919e90a57104334%7C1581672153%7C5184000%7CTue%2C+14-Apr-2020+09%3A22%3A33+GMT; uid_tt=04f0801635c409ce9c5180daf9175606; uid_tt_ss=04f0801635c409ce9c5180daf9175606; sid_tt=bfc2d5c6fcc89665f919e90a57104334; sessionid=bfc2d5c6fcc89665f919e90a57104334; sessionid_ss=bfc2d5c6fcc89665f919e90a57104334"
	# 	request_url = "https://api3-normal-c-hl.amemv.com/aweme/v1/aweme/detail/?version_code=9.7.1&js_sdk_version=1.49.0.2&app_name=aweme&vid=3ABAE60D-6E9B-4869-8A1F-AE942AA458BD&app_version=9.7.1&device_id=19783064087&channel=App%20Store&mcc_mnc=46002&aid=1128&screen_width=750&openudid=0c7416b27a11cef2b246db957cd633485bcaa486&cdid=1B42AE70-635A-4215-8C45-80247AD7D151&os_api=18&ac=WIFI&os_version=9.1&device_platform=iphone&build_number=97103&iid=103220293622&device_type=iPhone7,2&idfa=F9214093-EAC8-44A9-AA4D-78D6B5C1504B"

	# 	args = script.exports.getsign(request_url)

	# 	x_gorgon = args.get("X-Gorgon")
	# 	x_khronos = args.get("X-Khronos")

	# 	response = requests.post(
	# 		url=request_url,
	# 		data = {
	# 			'aweme_id': '6799885772775263502',
	# 			'request_tag_from': 'rn'
	# 		},
	# 		headers={
	# 			"Host": "api3-normal-c-hl.amemv.com",
	# 			"Connection": "keep-alive",
	# 			"Content-Length": "48",
	# 			"sdk-version": "1",
	# 			"x-Tt-Token": "00baf3423637f5dede7ed81ccbbec8934e176becc451e6fc2e8b4abbac4a0aeb7cba2386be1cd9f9d4f1ebcdf9e3fbf0d361",
	# 			"Content-Type": "application/x-www-form-urlencoded",
	# 			"User-Agent": "Aweme 9.7.1 rv:97103 (iPhone; iPhone OS 9.1; zh_CN) Cronet",
	# 			"X-SS-STUB": "20F2793977B83053D3C2F717FFF3C74D",
	# 			"X-SS-DP": "1128",
	# 			"x-tt-trace-id": "00-a846d24b0949b299a17ced7bf63a0468-a846d24b0949b299-01",
	# 			"Accept-Encoding": "gzip, deflate",
	# 			"Cookie": "d_ticket=234f072630b25b6600c3f9515f5198f5e396b; msh=tRHUW3RWjs3GF5Mm4br86RNYvzc; odin_tt=24d48ff9f3e47a57c802c4b339983e36a243edae352c60ba5bc6535f319f06a6a0fd8bebeeb2de05bb041525f2bdb75bdef92f384e2fc97a9c91a60181c22579; sessionid=baf3423637f5dede7ed81ccbbec8934e; sid_guard=baf3423637f5dede7ed81ccbbec8934e%7C1582516054%7C5184000%7CFri%2C+24-Apr-2020+03%3A47%3A34+GMT; sid_tt=baf3423637f5dede7ed81ccbbec8934e; uid_tt=f59ee0e9bf512bf64cc19e927beea342; install_id=103220293622; ttreq=1$bae403042f7014e59b816259b69f6e971eda8b8f",
	# 			"X-Khronos": x_khronos,
	# 			"X-Gorgon": x_gorgon
	# 		}
	# 	)
	# 	return response.text;
	elif action == "getsign":
		request_url = request.args.get("url")
		try:
			args = script.exports.getsign(request_url,json.dumps([]))
			x_gorgon = args.get("X-Gorgon")
			x_khronos = args.get("X-Khronos")
		except frida.InvalidOperationError as msg:
			print("[*] frida.InvalidOperationError")
			print(msg)
			return jsonify({
				"code": -1,
				"x_g": "",
				"x_k": "",
				"message": "frida.InvalidOperationError"
			})
		else:
			return jsonify({
				"code": 1,
				"x_g": x_gorgon,
				"x_k": x_khronos,
				"message": "success"
			})
	else:
		return jsonify({
			"code": 0,
			"data": [],
			"message": "no action"
		})


if __name__ == '__main__':
	app.run(host='0.0.0.0', port='9888')
