#!/usr/bin/env python

import http.client
import threading
import random
import queue
import html
import json
import time

direct = ["/authentication/guest",	#0
		  "/authentication/login",	#1
		  "/account/logout",		#2
		  "/cometd/handshake",		#3
		  "/cometd/connect",		#4
		  "/cometd/"]				#5

trusteds = ["pixie", "Aallii", "loVely gaK", "sweety gak", "Nazanin_", "Artist Painter", "azizi", "Araz"]

offence1 = ["fuck", "shit", "scum", "retarded", "ass", "arse", "gay", "homo", "rape"]
offence2 = ["sex", "cunt", "wank", "bitch"]
offence4 = ["whore", "dick", "cock", "penis", "slut"]
offence8 = [u"\u06A9\u06CC\u0631", u"\u06A9\u0648\u0633", u"\u062C\u0642", u"\u062C\u0646\u062F\u0647", u"\u06A9\u0648\u0646", u"\u0645\u0645\u0647", "kir", "kos", "jaq", "jende"]

data_q = queue.Queue()
task_q = queue.Queue()

def compare_strings(origin, given):
	temp = given
	if len(origin) / len(given) >= 4:
		return False
	for char in origin.lower():
		if char == temp[0]:
			if len(temp) <= 1:
				return True
			temp = temp[1:]
	return False

class Shared():
	def __init__(self):
		self.exit = False
		self.cookie = ''
		self.client = ''
		self.cnid = 2
		self.cnid_lock = threading.Lock()
		self.data_lock = threading.Lock()

	def inc_cnid(self):
		self.cnid_lock.acquire()
		text = str(self.cnid)
		self.cnid += 1
		self.cnid_lock.release()
		return text

	def set_cnid(self):
		self.cnid_lock.acquire()
		self.cnid = 2
		self.cnid_lock.release()
		return

	def get_cnid(self):
		self.cnid_lock.acquire()
		cnid = self.cnid
		self.cnid_lock.release()
		return cnid

	def set_cookie(self, new_cookie):
		self.data_lock.acquire()
		if self.cookie != '':
			self.cookie = self.cookie + ";" + new_cookie
		else:
			self.cookie = new_cookie
		self.data_lock.release()
		return

	def get_cookie(self):
		self.data_lock.acquire()
		cookie = self.cookie
		self.data_lock.release()
		return cookie

	def set_client(self, new_client):
		self.data_lock.acquire()
		self.client = new_client
		self.data_lock.release()
		return

	def get_client(self):
		self.data_lock.acquire()
		client = self.client
		self.data_lock.release()
		return client

class User():
	def __init__(self, name, uuid, isGuest):
		self.name = name
		self.uuid = uuid
		self.last_text = ''
		self.repeated = 0
		self.isGuest = isGuest
		self.capital = 0
		self.in_mute = 0
		self.swear = 0
		self.mute = False
		self.spam = 0
		if isGuest == True:
			self.rep_limit = 2
			self.cap_limit = 4
			self.swr_limit = 2
			self.mut_limit = 8
		else:
			self.rep_limit = 4
			self.cap_limit = 8
			self.swr_limit = 8
			self.mut_limit = 4
		if self.name in trusteds:
			self.isTrusted = True
		else:
			self.isTrusted = False

	def mute_user(self):
		self.mute = True
		self.mut_limit = 256
		return

	def unmute_user(self):
		self.mute = False
		self.mut_limit = 4
		self.repeated = 0
		self.capital = 0
		self.in_mute = 0
		self.swear = 0
		return

	def trust_user(self):
		self.isTrusted = True
		return

	def distrust_user(self):
		self.isTrusted = False
		return
		
	def check_text(self, text):
		if self.isTrusted == True:
			self.last_text = text
			self.mute = False
			return
		if self.last_text == text:
			self.repeated += 1
		if text.isupper() == True:
			self.capital += 1
		low_case = text.lower()
		words = low_case.split()
		for abuse in offence1:
			for word in words:
				if word.find(abuse) >= 0:
					self.swear += 1
		for abuse in offence2:
			for word in words:
				if word.find(abuse) >= 0:
					self.swear += 2
		for abuse in offence4:
			for word in words:
				if word.find(abuse) >= 0:
					self.swear += 4
		for abuse in offence8:
			for word in words:
				if word.find(abuse) >= 0:
					self.swear += 8
		if self.repeated >= self.rep_limit or self.capital >= self.cap_limit or self.swear >= self.swr_limit:
			self.repeated = 0
			self.capital = 0
			self.in_mute = 0
			self.swear = 0
			self.mute = True
			self.spam += 1
		if self.in_mute >= self.mut_limit:
			self.repeated = 0
			self.capital = 0
			self.in_mute = 0
			self.swear = 0
			self.mute = False
		self.last_text = text
		return

class Room():
	def __init__(self):
		self.users = []
		self.texts = {}
		self.banned_uuids = {}

	def seek_banned_uuid(self, name):
		for uuid in self.banned_uuids.keys():
			if compare_strings(self.banned_uuids[uuid], name) == True:
				return self.banned_uuids[uuid], uuid
		return None, None

	def seek_text_by_name(self, name):
		for uuid in self.texts.keys():
			if compare_strings(self.texts[uuid], name) == True:
				return self.texts[uuid], uuid
		return None, None

	def seek_user_by_uuid(self, uuid):
		for i in range(len(self.users)):
			if self.users[i].uuid == uuid:
				return self.users[i], i
		return None, -1

	def seek_user_by_name(self, name):
		for i in range(len(self.users)):
			if compare_strings(self.users[i].name, name) == True:
				return self.users[i], i
		return self.find_user_by_name(name)

	def find_user_by_name(self, name):
		body = "targetUsername=" + name
		seek = http.client.HTTPConnection("e-chat.co")
		seek.connect()
		headers = {}
		headers["Host"] = "e-chat.co"
		headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
		headers["Content-Length"] = str(len(body))
		body = body.encode('utf-8')
		seek.request("POST", "/search/users", body, headers)
		rspn = seek.getresponse()
		status = rspn.status
		reason = rspn.reason
		hdlist = rspn.getheaders()
		stream = rspn.read()
		rspn.close()
		stream = stream.decode('utf-8')
		rspn = html.unescape(stream)
		index = 0
		start = 0
		while index < len(rspn):
			start = rspn.find("\"userUuid\"", start)
			if start < 0:
				break
			end = rspn.find("\",", start)
			if end < 0:
				break
			user_uuid = rspn[start + 12:end]
			start = end
			start = rspn.find("\"username\"", start)
			end = rspn.find("\"}", start)
			user_name = rspn[start + 12:end]
			user_name = html.unescape(user_name)
			user_name = user_name.lower()
			if user_name == name.lower():
				return User(user_name, user_uuid, False), -1
		return None, -1

	def add_user(self, name, uuid, isGuest):
		user = User(name, uuid, isGuest)
		self.users.append(user)
		return

	def del_user(self, index):
		try: user = self.users.pop(index)
		except: print("[error]: given index is out of range")
		return

	def add_text(self, name, uuid):
		self.texts[uuid] = name
		return

	def del_text(self, uuid):
		text = self.texts.pop(uuid, None)
		return

	def add_banned_uuid(self, name, uuid):
		self.banned_uuids[uuid] = name
		return

	def del_banned_uuid(self, uuid):
		name = self.banned_uuids.pop(uuid, None)
		return

class Observer(threading.Thread):
	def __init__(self, usrnme, passwd, roomId):
		threading.Thread.__init__(self)
		self.usrnme = usrnme
		self.passwd = passwd
		self.roomId = roomId
		self.cookie = ''
		self.client = ''
		self.count = 2
		self.alive = False
		self.conn = http.client.HTTPConnection("e-chat.co")
		self.conn.connect()

	def send_recv(self, method, iLink, body):
		headers = {}
		headers["Host"] = "e-chat.co"
		if iLink < 2:
			headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
		elif iLink > 2:
			headers["Content-Type"] = "application/json; charset=UTF-8"
		if iLink != 2:
			headers["Content-Length"] = str(len(body))
			headers["Connection"] = "keep-alive"
			body = body.encode('utf-8')
		if self.cookie != "":
			headers["Cookie"] = self.cookie
		self.conn.request(method, direct[iLink], body, headers)
		rspn = self.conn.getresponse()
		status = rspn.status
		reason = rspn.reason
		hdlist = rspn.getheaders()
		stream = rspn.read()
		rspn.close()
		for tup in hdlist:
			if "Set-Cookie" in tup:
				shr.set_cookie(tup[1][:tup[1].find(";")])
				self.cookie = shr.get_cookie()
		return status, reason, stream.decode('utf-8')

	def guest(self):
		body = "username=" + self.usrnme
		return self.send_recv("POST", 0, body)

	def login(self):
		body = "username=" + self.usrnme + "&password=" + self.passwd + "&rememberAuthDetails=false"
		return self.send_recv("POST", 1, body)

	def logout(self):
		status, reason, stream = self.send_recv("GET", 2, None)
		self.conn.close()
		return status, reason, stream

	def handshake(self):
		shr.set_cnid()
		body = "[{\"ext\":{\"chatroomId\":" + self.roomId + "},\"version\":\"1.0\",\"minimumVersion\":\"0.9\",\"channel\":\"/meta/handshake\",\"supportedConnectionTypes\":[\"long-polling\",\"callback-polling\"],\"advice\":{\"timeout\":60000,\"interval\":0},\"id\":\"1\"}]"
		status, reason, stream = self.send_recv("POST", 3, body)
		start = stream.find("\"clientId\"")
		end = stream.find(",", start)
		self.client = stream[start:end]
		shr.set_client(self.client)
		return status, reason, stream

	def metacon(self):
		body = "[{\"channel\":\"/meta/connect\",\"connectionType\":\"long-polling\",\"advice\":{\"timeout\":0},\"id\":\"" + shr.inc_cnid() + "\"," + self.client + "}]"
		return self.send_recv("POST", 4, body)

	def connect(self):
		body = "[{\"channel\":\"/meta/connect\",\"connectionType\":\"long-polling\",\"id\":\"" + shr.inc_cnid() + "\"," + self.client + "}]"
		return self.send_recv("POST", 4, body)

	def context(self):
		body = "[{\"channel\":\"/service/user/context/self/complete\",\"data\":{},\"id\":\"" + shr.inc_cnid() + "\"," + self.client + "}]"
		return self.send_recv("POST", 5, body)

	def join_room(self):
		print("[debug]: trying to join room")
		self.alive = False
		self.conn = http.client.HTTPConnection("e-chat.co")
		self.conn.connect()
		if self.passwd != "":
			status, reason, stream = self.login()
		else:
			status, reason, stream = self.guest()
		status, reason, stream = self.handshake()
		status, reason, stream = self.metacon()
		status, reason, stream = self.context()
		data = json.loads(stream)
		data_q.put(data[0])
		self.alive = True
		shr.exit = False
		return

	def run(self):
		self.join_room()
		while self.alive == True:
			try:
				status, reason, stream = self.connect()
			except:
				print("[error]: connection is lost")
				self.conn.close()
				self.join_room()
				continue
			data = json.loads(stream)
			for obj in data:
				if obj['channel'] != "/meta/connect":
					data_q.put(obj)
				else:
					self.alive = obj['successful']
			if shr.get_cnid() > 256:
				print("[debug]: maximum number of requests reached")
				self.conn.close()
				self.join_room()
			if shr.exit == True:
				self.alive = False
		data_q.put(None)
		task_q.put(None)
		shr.exit = True
		status, reason, stream = self.logout()
		return

class Processor(threading.Thread):
	def __init__(self, usrnme, passwd, roomId):
		threading.Thread.__init__(self)
		self.usrnme = usrnme
		self.passwd = passwd
		self.roomId = roomId
		self.locked = False
		self.filter = False
		self.alive = False
		self.room = Room()
		self.set_locked = 0
		self.set_filter = 0
		self.timeout = 120

	def run(self):
		while True:
			obj = data_q.get()
			if obj == None:
				break
			elif obj['channel'] == "/chatroom/message/add/" + self.roomId:
				try:
					user_uuid = obj['data']['userUuid']
					user_name = html.unescape(obj['data']['username'])
					user_text = html.unescape(obj['data']['messageBody'])
					self.message_add(user_uuid, user_name, user_text)
				except:
					print("[error]: json format has changed for", obj['channel'])
					pass
			elif obj['channel'] == "/chatroom/user/joined/" + self.roomId:
				try:
					user_uuid = obj['data']['userUuid']
					user_name = html.unescape(obj['data']['username'])
					isGuest = obj['data']['isGuest']
					self.user_join(user_uuid, user_name, isGuest)
				except:
					print("[error]: json format has changed for", obj['channel'])
					pass
			elif obj['channel'] == "/chatroom/user/left/" + self.roomId:
				try:
					self.user_left(obj['data'])
				except:
					print("[error]: json format has changed for", obj['channel'])
					pass
			elif obj['channel'] == "/service/conversation/message":
				try:
					self.private_add(obj['data']['msg'], obj['data']['key'])
				except:
					print("[error]: json format has changed for", obj['channel'])
					pass
			elif obj['channel'] == "/service/user/context/self/complete":
				try:
					users = obj['data']['chatroomContext']['data']['users']
					texts = obj['data']['chatroomContext']['data']['messages']
					banned_uuids = obj['data']['chatroomBannedUuids']
					self.prepare_list(users, texts, banned_uuids)
				except:
					print("[error]: json format has changed for", obj['channel'])
					pass
			if self.locked == True and int(time.time()) - self.set_locked > self.timeout:
				self.locked = False
				self.set_locked = 0
				for uuid in self.room.banned_uuids.keys():
					task_q.put([1, uuid])
				self.room.banned_uuids.clear()
			if self.filter == True and int(time.time()) - self.set_filter > self.timeout:
				self.filter = False
				self.set_filter = 0
		return

	def prepare_list(self, users, texts, banned_uuids):
		self.room.users.clear()
		self.room.texts.clear()
		self.room.banned_uuids.clear()
		for uuid in users.keys():
			self.room.add_user(users[uuid]['username'], uuid, users[uuid]['isGuest'])
		for text in texts:
			self.room.add_text(text['username'], text['userUuid'])
		for uuid in banned_uuids:
			self.room.add_banned_uuid("", uuid)
		return

	def user_join(self, user_uuid, user_name, isGuest):
		if self.locked == True or (self.filter == True and isGuest == True):
			task_q.put([0, user_uuid])
			self.room.add_banned_uuid(user_name, user_uuid)
		else:
			self.room.add_user(user_name, user_uuid, isGuest)
			print("[debug]: user joined")
		return

	def user_left(self, user_uuid):
		user, index = self.room.seek_user_by_uuid(user_uuid)
		self.room.del_user(index)
		print("[debug]: user left")
		return

	def message_add(self, user_uuid, user_name, user_text):
		user, index = self.room.seek_user_by_uuid(user_uuid)
		if index >= 0:
			self.room.users[index].check_text(user_text)
			if self.room.users[index].mute == True:
				task_q.put([2, user_uuid])
				self.room.users[index].in_mute += 1
				self.room.del_text(user_uuid)
			else:
				self.room.add_text(user_name, user_uuid)
		else:
			self.room.add_user(user_name, user_uuid, False)
			print("[error]: user added")
		return

	def private_add(self, msg, key):
		user_ordr = msg['o'] - 1
		user_text = html.unescape(msg['m'])
		user_text = user_text.lower()
		user_text = user_text.replace("\\\"", "\"")
		if msg['o'] == 1:
			user_uuid = key[:36]
		elif msg['o'] == 2:
			user_uuid = key[36:]
		else:
			print("[error]: unexpected order", msg['o'])
			if key[:36] != "2abcce47-eda0-443d-a382-78bb4b45045e": #"9cd92a17-22c3-4c83-ab26-32bef7b01cc0"
				user_uuid = key[:36]
			else:
				user_uuid = key[36:]
		if user_text[:4] == "ban ":
			self.make_task_0(user_text[4:], user_uuid)
		elif user_text[:6] == "unban ":
			self.make_task_1(user_text[6:], user_uuid)
		elif user_text[:7] == "remove ":
			self.make_task_2(user_text[7:], user_uuid)
		elif user_text[:6] == "trust ":
			self.make_task_3(3, user_text[6:], user_uuid)
		elif user_text[:9] == "distrust ":
			self.make_task_3(4, user_text[9:], user_uuid)
		elif user_text[:5] == "mute ":
			self.make_task_3(5, user_text[5:], user_uuid)
		elif user_text[:7] == "unmute ":
			self.make_task_3(6, user_text[7:], user_uuid)
		elif user_text[:7] == "filter ":
			self.update_filter(user_text[7:], user_uuid)
		elif user_text[:8] == "timeout ":
			self.set_timeout(user_text[8:], user_uuid)
		elif user_text[:4] == "say ":
			self.say_text(user_text[4:], user_uuid)
		elif user_text == "lock":
			self.update_locked(True, user_uuid)
		elif user_text == "unlock":
			self.update_locked(False, user_uuid)
		elif user_text == "list":
			self.list_users(user_uuid)
		elif user_text == "clear":
			self.clear_texts(user_uuid)
		elif user_text == "free":
			self.unban_all(user_uuid)
		elif user_text == "restart":
			self.restart_machine(user_uuid)
		elif user_text == "help":
			self.help_user(user_uuid)
		else:
			task_q.put([5, user_uuid, "can not understand your order, type help if you need it"])
		return

	def list_users(self, user_uuid):
		for user in self.room.users:
			text = user.uuid + " : " + json.dumps(user.name).strip("\"")
			task_q.put([5, user_uuid, text])
		if len(self.room.users) <= 0:
			task_q.put([5, user_uuid, "room is quite empty"])
		return

	def clear_texts(self, user_uuid):
		for uuid in self.room.texts.keys():
			task_q.put([2, uuid])
		self.room.texts.clear()
		task_q.put([5, user_uuid, "room is fairly cleared"])
		return

	def unban_all(self, user_uuid):
		for uuid in self.room.banned_uuids.keys():
			task_q.put([1, uuid])
		self.room.banned_uuids.clear()
		task_q.put([5, user_uuid, "ban list is cleared"])
		return

	def say_text(self, user_text, user_uuid):
		task_q.put([8, user_text])
		task_q.put([5, user_uuid, "the given text has been posted in public chat"])
		return

	def set_timeout(self, period, user_uuid):
		try:
			self.timeout = int(period) * 60
			task_q.put([5, user_uuid, "timeout period has been updated"])
		except:
			task_q.put([5, user_uuid, "timeout period must be a plain number indicating minutes only"])
		return

	def restart_machine(self, user_uuid):
		task_q.put([5, user_uuid, "the bot will restart within a minute"])
		shr.exit = True
		return

	def update_filter(self, flag, user_uuid):
		last_state = self.filter
		if flag == "on":
			self.filter = True
			self.set_filter = int(time.time())
			if last_state == True:
				task_q.put([5, user_uuid, "guest filter has been set on already"])
			else:
				task_q.put([5, user_uuid, "guest filter is set on"])
		elif flag == "off":
			self.filter = False
			self.set_filter = 0
			if last_state == False:
				task_q.put([5, user_uuid, "guest filter has been set off already"])
			else:
				task_q.put([5, user_uuid, "guest filter is set off"])
		else:
			task_q.put([5, user_uuid, "type filter on/off"])
		return

	def update_locked(self, flag, user_uuid):
		last_state = self.locked
		if flag == True:
			self.locked = True
			self.set_locked = int(time.time())
			if last_state == True:
				task_q.put([5, user_uuid, "room has been locked already"])
			else:
				task_q.put([5, user_uuid, "room is locked"])
		elif flag == False:
			self.locked = False
			self.set_locked = 0
			if last_state == False:
				task_q.put([5, user_uuid, "room has been unlocked already"])
			else:
				for uuid in self.room.banned_uuids.keys():
					task_q.put([1, uuid])
				self.room.banned_uuids.clear()
				task_q.put([5, user_uuid, "room is unlocked"])
		return

	def help_user(self, user_uuid):
		task_q.put([5, user_uuid, "ban [username]: tries to ban the specified user"])
		task_q.put([5, user_uuid, "unban [username]: tries to unban the specified user"])
		task_q.put([5, user_uuid, "remove [username]: tries to remove the messages sent by the specified user"])
		task_q.put([5, user_uuid, "trust [username]: stops checking texts by the specified user for spam treats"])
		task_q.put([5, user_uuid, "distrust [username]: resumes checking texts by the specified user for spam treats"])
		task_q.put([5, user_uuid, "mute [username]: removes texts by the specified user right at the time they appear"])
		task_q.put([5, user_uuid, "unmute [username]: unmutes the specified user"])
		task_q.put([5, user_uuid, "lastseen [username]: due to user privacy issues, this command is currently deactivated"])
		task_q.put([5, user_uuid, "say [text]: posts the given text in public chat"])
		task_q.put([5, user_uuid, "filter [on/off]: sets guest filter on or off, it remains on for 2 minutes"])
		task_q.put([5, user_uuid, "lock: stops users from joining the room, it remains on for 2 minutes"])
		task_q.put([5, user_uuid, "unlock: allows all users to join the room, clears ban list for false user bans"])
		task_q.put([5, user_uuid, "timeout [minutes]: sets prefered timeout for guest filter and room lockout"])
		task_q.put([5, user_uuid, "clear: removes all texts in the main chat box"])
		task_q.put([5, user_uuid, "list: lists some info about all the users that the bot currently inspects"])
		task_q.put([5, user_uuid, "restart: restarts the bots and all users logs will be lost in return"])
		return

	def make_task_0(self, target, user_uuid):
		user = None	
		if len(target) == 36 and target[8] == "-" and target[13] == "-" and target[18] == "-" and target[23] == "-":
			user, index = self.seek_user_by_uuid(target)
			user = User(None, target, True)
		else:
			user, index = self.room.seek_user_by_name(target)
		if user != None:
			task_q.put([0, user.uuid])
			task_q.put([5, user_uuid, "user was found"])
			self.room.add_banned_uuid(user.name, user.uuid)
			self.room.del_user(index)
		else:
			task_q.put([5, user_uuid, "no such user was found"])
		return

	def make_task_1(self, target, user_uuid):
		target_user_uuid = None
		if len(target) == 36 and target[8] == "-" and target[13] == "-" and target[18] == "-" and target[23] == "-":
			target_user_uuid = target
		else:
			name, target_user_uuid = self.room.seek_banned_uuid(target)
		if target_user_uuid != None:
			task_q.put([1, target_user_uuid])
			task_q.put([5, user_uuid, "user was found"])
			self.room.del_banned_uuid(target_user_uuid)
		else:
			user, index = self.room.find_user_by_name(target)
			if user != None:
				task_q.put([1, user.uuid])
				task_q.put([5, user_uuid, "user was found"])
				self.room.del_banned_uuid(user.uuid)
			else:
				task_q.put([5, user_uuid, "no such user was found"])
		return

	def make_task_2(self, target, user_uuid):
		target_user_uuid = None
		if len(target) == 36 and target[8] == "-" and target[13] == "-" and target[18] == "-" and target[23] == "-":
			target_user_uuid = target
		else:
			name, target_user_uuid = self.room.seek_text_by_name(target)
		if target_user_uuid != None:
			task_q.put([2, target_user_uuid])
			task_q.put([5, user_uuid, "user was found"])
			self.room.del_text(target_user_uuid)
		else:
			user, index = self.room.find_user_by_name(target)
			if user != None:
				task_q.put([2, user.uuid])
				task_q.put([5, user_uuid, "user was found"])
				self.room.del_text(user.uuid)
			else:
				task_q.put([5, user_uuid, "no such user was found"])
		return

	def make_task_3(self, task, target, user_uuid):
		user = None
		if len(target) == 36 and target[8] == "-" and target[13] == "-" and target[18] == "-" and target[23] == "-":
			user, index = self.room.seek_user_by_uuid(target)
		else:
			user, index = self.room.seek_user_by_name(target)
		if index >= 0:
			if task == 3:
				self.room.users[index].trust_user()
			elif task == 4:
				self.room.users[index].distrust_user()
			elif task == 5:
				self.room.users[index].mute_user()
			elif task == 6:
				self.room.users[index].unmute_user()
			task_q.put([5, user_uuid, "user was found"])
		else:
			task_q.put([5, user_uuid, "no such user was found"])
		return

class Operator(threading.Thread):
	def __init__(self, usrnme, passwd, roomId):
		threading.Thread.__init__(self)
		self.usrnme = usrnme
		self.passwd = passwd
		self.roomId = roomId
		self.cookie = ''
		self.client = ''
		self.count = 2
		self.alive = False
		self.comt = http.client.HTTPConnection("e-chat.co")
		self.comt.connect()

	def send_recv(self, method, iLink, body):
		headers = {}
		headers["Host"] = "e-chat.co"
		headers["Content-Type"] = "application/json; charset=UTF-8"
		headers["Content-Length"] = str(len(body))
		headers["Connection"] = "keep-alive"
		body = body.encode('utf-8')
		headers["Cookie"] = shr.get_cookie()
		trynum = 0
		while trynum < 5:
			try:
				trynum += 1
				self.comt.request(method, direct[iLink], body, headers)
				rspn = self.comt.getresponse()
				status = rspn.status
				reason = rspn.reason
				hdlist = rspn.getheaders()
				stream = rspn.read()
				rspn.close()
				trynum = 6
			except:
				self.comt.close()
				self.comt = http.client.HTTPConnection("e-chat.co")
				self.comt.connect()
				continue
		return status, reason, stream.decode('utf-8')

	def message(self, text):
		body = "[{\"channel\":\"/service/chatroom/message\",\"data\":{\"messageBody\":\"" + text + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_client() + "}]"
		return self.send_recv("POST", 5, body) #body.encode('utf-8')

	def open_box(self, convId):
		body = "[{\"channel\":\"/service/conversation/opened\",\"data\":{\"conversationUserUuid\":\"" + convId + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_client() + "}]"
		return self.send_recv("POST", 5, body)

	def clos_box(self, convId):
		body = "[{\"channel\":\"/service/conversation/closed\",\"data\":{\"conversationUserUuid\":\"" + convId + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_client() + "}]"
		return self.send_recv("POST", 5, body)

	def private(self, convId, text):
		body = "[{\"channel\":\"/service/conversation/message\",\"data\":{\"conversationUserUuid\":\"" + convId + "\",\"messageBody\":\"" + text + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_client() + "}]"
		return self.send_recv("POST", 5, body) #body.encode('utf-8')	

	def append_friend(self, friendUuid):
		body = "[{\"channel\":\"/service/friends/add\",\"data\":{\"userUuid\":\"" + friendUuid + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_client() + "}]"
		return self.send_recv("POST", 5, body)

	def remove_friend(self, friendUuid):
		body = "[{\"channel\":\"/service/friends/remove\",\"data\":{\"userUuid\":\"" + friendUuid + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_client() + "}]"
		return self.send_recv("POST", 5, body)

	def remove_text(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/messages/remove\",\"data\":{\"targetUserUuid\":\"" + targetUuid + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_client() + "}]"
		return self.send_recv("POST", 5, body)

	def remove_ban(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/ban/remove\",\"data\":{\"targetUserUuid\":\"" + targetUuid + "\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_client() + "}]"
		return self.send_recv("POST", 5, body)

	def append_ban(self, targetUuid):
		body = "[{\"channel\":\"/service/moderator/ban/add\",\"data\":{\"targetUserUuid\":\"" + targetUuid +"\"},\"id\":\"" + shr.inc_cnid() + "\"," + shr.get_client() + "}]"
		return self.send_recv("POST", 5, body)

	def run(self):
		time.sleep(2)
		self.cookie = shr.get_cookie()
		self.client = shr.get_client()
		while True:
			cmd = task_q.get()
			if cmd == None:
				break
			elif cmd[0] == 0:
				status, reason, stream = self.append_ban(cmd[1])
			elif cmd[0] == 1:
				status, reason, stream = self.remove_ban(cmd[1])
			elif cmd[0] == 2:
				status, reason, stream = self.remove_text(cmd[1])
			elif cmd[0] == 3:
				status, reason, stream = self.remove_friend(cmd[1])
			elif cmd[0] == 4:
				status, reason, stream = self.append_friend(cmd[1])
			elif cmd[0] == 5:
				status, reason, stream = self.private(cmd[1], cmd[2])
			elif cmd[0] == 6:
				status, reason, stream = self.clos_box(cmd[1])
			elif cmd[0] == 7:
				status, reason, stream = self.open_box(cmd[1])
			elif cmd[0] == 8:
				status, reason, stream = self.message(cmd[1])
		return

shr = Shared()

def main():
	usrnme = "Iran_Is_Safe"
	passwd = "frlm"
	roomId = "215315"
	pod = Observer(usrnme, passwd, roomId)
	pod.start()
	mod = Processor(usrnme, passwd, roomId)
	mod.start()
	cod = Operator(usrnme, passwd, roomId)
	cod.start()
	return

if __name__ == '__main__':
	main()
