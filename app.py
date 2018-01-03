import http.client
import threading
import difflib
import html
import json

urls = [
       '/authentication/guest',   #0
       '/authentication/login',   #1
       '/search/users',           #2
       '/cometd/handshake',       #3
       '/cometd/connect',         #4
       '/cometd/',                #5
       '/account/logout',         #6
       '/'                        #7
       ]

class Crawler(threading.Thread):

    def __init__(self, auth_cookie, room_numb):
        threading.Thread.__init__(self)
        self.auth_cookie = auth_cookie
        self.room_numb = room_numb
        self.isRunning = False
        self.client_id = None
        self.ids_count = 0
        self.cookies = None
        self.friends = list()
        self.conn = http.client.HTTPConnection('e-chat.co', port=80)
        return

    def send_receive(self, method, index, body):
        #print('[debug]: trying to send data')
        #print(body)
        headers, stream = self.build_request_headers(index, body)
        headers, stream = self.request_response(method, urls[index], stream, headers)
        if headers == None or stream == None:
            return None
        if index == 3 or index == 7:
            self.update_cookies(headers)
        #print('[debug]: received response data')
        #print(stream.decode('utf-8'))
        return stream.decode('utf-8')

    def update_cookies(self, headers):
        #print('[debug]: headers for invoked update are as', headers)
        for pair in headers:
            if pair[0] == 'Set-Cookie':
                new_cookie = pair[1][:pair[1].find(';')]
                #self.cookies = self.cookies[:self.cookies.find(';')]
                #print('[debug]: cookies before update are as', self.cookies)
                self.cookies = self.cookies + '; ' + new_cookie
                #print('[debug]: cookies after update are as', self.cookies)
        return

    def request_response(self, method, url, body, headers):
        try_count = 8
        while try_count > 0:
            try:
                try_count -= 1
                #print('[debug]: trying to send data, attempt', 8 - try_count)
                self.conn.request(method, url, body, headers)
                respon = self.conn.getresponse()
                status = respon.status
                reason = respon.reason
                header = respon.getheaders()
                stream = respon.read()
                respon.close()
                #print('[debug]: succeeded in sending data, attempt', 8 - try_count)
                return header, stream
            except:
                status = self.refresh_connection()
                continue
        #print('[debug]: failed to send data, attempt', 8 - try_count)
        return None, None

    def refresh_connection(self):
        try:
            self.conn.close()
            self.conn = http.client.HTTPConnection('e-chat.co', port=80)
            self.conn.connect()
            return True
        except:
            return False

    def build_request_headers(self, index, body):
        headers = {}
        headers['Host'] = 'e-chat.co'
        if index < 3: #guest, login, search
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        elif index < 6: #handshake, connect, cometd
            headers['Content-Type'] = 'application/json; charset=UTF-8'
        if index != 2 and index != 6: #except search, logout
            headers['Connection'] = 'keep-alive'
        if body != None:
            headers['Content-Length'] = str(len(body))
            body = body.encode('utf-8')
        if self.cookies != None:
            headers['Cookie'] = self.cookies
        return headers, body

    def manual_user_login(self):
        self.open_session()
        stream = self.send_receive('GET', 7, None)
        return (self.cookies.find('JSESSIONID') != -1)

    def checked_user_login(self):
        for test in range(4):
            if self.user_login() == '100':
                return True
        return False

    def open_session(self):
        self.client_id = None
        self.ids_count = 0
        #self.cookies = 'echat-authentication-cookie=cacb05c0-1801-425e-8485-2b0352afc517' #blackish
        #self.cookies = 'echat-authentication-cookie=b3acd112-2f43-475e-8de4-bb27794acab5' #manonic
        #self.cookies = 'echat-authentication-cookie=27b78658-b65c-44d2-a602-23cb11d67619' #Iran_Is_Safe
        self.cookies = self.auth_cookie
        self.conn = http.client.HTTPConnection('e-chat.co', port=80)
        self.conn.connect()
        return

    def close_session(self):
        self.client_id = None
        self.ids_count = 0
        self.cookies = None
        self.conn.close()
        return

    def user_login(self):
        if self.pass_word == None:
            body = 'username=' + self.user_name
        else:
            body = 'username=' + self.user_name + '&password=' + self.pass_word + '&rememberAuthDetails=false'
        self.open_session()
        return self.send_receive('POST', 1, body)

    def user_logout(self):
        stream = self.send_receive('GET', 6, None)
        self.close_session()
        return stream

    def checked_room_handshake(self):
        self.ids_count = 0
        stream = self.room_handshake()
        if stream == None:
            return False
        st = stream.find('\"clientId\"')
        en = stream.find(',', st)
        if st == -1 or en == -1:
            return False
        self.client_id = stream[st:en]
        return True

    def room_handshake(self):
        body = '[{\"ext\":{\"chatroomId\":' + self.room_numb + '},\"version\":\"1.0\",\"minimumVersion\":\"0.9\",\"channel\":\"/meta/handshake\",\"supportedConnectionTypes\":[\"long-polling\",\"callback-polling\"],\"advice\":{\"timeout\":60000,\"interval\":0},\"id\":\"1\"}]'
        return self.send_receive('POST', 3, body)

    def meta_connect(self):
        self.ids_count += 1
        body = '[{\"channel\":\"/meta/connect\",\"connectionType\":\"long-polling\",\"advice\":{\"timeout\":0},\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        return self.send_receive('POST', 4, body)

    def room_connect(self):
        self.ids_count += 1
        body = '[{\"channel\":\"/meta/connect\",\"connectionType\":\"long-polling\",\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        return self.send_receive('POST', 4, body)

    def get_context(self):
        self.ids_count += 1
        body = '[{\"channel\":\"/service/user/context/self/complete\",\"data\":{},\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        stream = self.send_receive('POST', 5, body)
        self.handle_json(json.loads(stream)[0])
        return stream

    def send_public_text(self, text):
        self.ids_count += 1
        body = '[{\"channel\":\"/service/chatroom/message\",\"data\":{\"messageBody\":\"' + text + '\"},\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        return self.send_receive('POST', 5, body)

    def send_private_text(self, conv_uuid, text):
        self.ids_count += 1
        body = '[{\"channel\":\"/service/conversation/message\",\"data\":{\"conversationUserUuid\":\"' + conv_uuid + '\",\"messageBody\":\"' + text + '\"},\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        return self.send_receive('POST', 5, body)

    def open_chat_box(self, conv_uuid):
        self.ids_count += 1
        body = '[{\"channel\":\"/service/conversation/opened\",\"data\":{\"conversationUserUuid\":\"' + conv_uuid + '\"},\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        return self.send_receive('POST', 5, body)

    def close_chat_box(self, conv_uuid):
        self.ids_count += 1
        body = '[{\"channel\":\"/service/conversation/closed\",\"data\":{\"conversationUserUuid\":\"' + conv_uuid + '\"},\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        return self.send_receive('POST', 5, body)

    def append_friend(self, friend_uuid, friend_name):
        friend = dict()
        friend['uuid'] = friend_uuid
        friend['name'] = friend_name
        friend['isOnline'] = False
        self.friends.append(friend)
        self.ids_count += 1
        stream = self.open_chat_box(friend_uuid)
        stream = self.send_private_text(friend_uuid, 'hello ' + friend_name)
        stream = self.send_private_text(friend_uuid, 'from now on i am a forced friend of yours')
        body = '[{\"channel\":\"/service/friends/add\",\"data\":{\"userUuid\":\"' + friend_uuid + '\"},\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        return self.send_receive('POST', 5, body)

    def remove_friend(self, friend_uuid):
        for friend in self.friends:
            if friend['uuid'] == friend_uuid:
                self.friends.remove(friend)
        stream = self.send_private_text(friend_uuid, 'it\'s been such an honour to befriended by you')
        stream = self.send_private_text(friend_uuid, 'alas our friendship is not going to last forever')
        stream = self.close_chat_box(friend_uuid)
        self.ids_count += 1
        body = '[{\"channel\":\"/service/friends/remove\",\"data\":{\"userUuid\":\"' + friend_uuid + '\"},\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        return self.send_receive('POST', 5, body)

    def append_ban(self, target_uuid):
        self.ids_count += 1
        body = '[{\"channel\":\"/service/moderator/ban/add\",\"data\":{\"targetUserUuid\":\"' + target_uuid + '\"},\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        return self.send_receive('POST', 5, body)

    def remove_ban(self, target_uuid):
        self.ids_count += 1
        body = '[{\"channel\":\"/service/moderator/ban/remove\",\"data\":{\"targetUserUuid\":\"' + target_uuid + '\"},\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        return self.send_receive('POST', 5, body)

    def remove_public_text(self, target_uuid):
        self.ids_count += 1
        body = '[{\"channel\":\"/service/moderator/messages/remove\",\"data\":{\"targetUserUuid\":\"' + target_uuid + '\"},\"id\":\"' + str(self.ids_count) + '\",' + self.client_id + '}]'
        return self.send_receive('POST', 5, body)

    def join_room(self):
        print('[debug]: trying to join room')
        if self.manual_user_login() == False:
            print('[error]: failed to login')
            return False
        if self.checked_room_handshake() == False:
            print('[error]: failed at handshake')
            return False
        if self.meta_connect() == None:
            print('[error]: failed to connect')
            return False
        if self.get_context() == None:
            print('[error]: failed to get context')
            return False
        print('[debug]: successfully joined room')
        return True

    def run(self):
        self.isRunning = self.join_room()
        while self.isRunning == True:
#            print('[debug]: awaiting new data')
            stream = self.room_connect()
            if stream == None:
                print('[error]: connection is lost')
                self.isRunning = self.join_room()
                continue
#            print('[debug]: received new data')
            if self.load_json(stream) == False:
                print('[debug]: connection is lost')
                self.isRunning = self.join_room()
            if self.ids_count >= 256:
                print('[debug]: maximum number of requests reached')
                self.isRunning = self.join_room()
        print('[debug]: failed to join room')
        return

    def load_json(self, stream):
        try:
            data = json.loads(stream)
            for obj in data:
                if obj['channel'] == '/meta/connect':
                    return obj['successful']
                else:
                    self.handle_json(obj)
        except:
            print('[error]: invalid json string')
        return False

    def handle_json(self, obj):
        if obj == None:
            self.isRunning = False
#        elif obj['channel'] == '/chatroom/message/add/' + self.room_numb:
#            try:
#                self.received_public_message(obj['data'])
#            except:
#                print('[error]: json format has changed for', obj['channel'])
#        elif obj['channel'] == '/chatroom/user/joined/' + self.room_numb:
#            try:
#                self.user_joined(obj['data'])
#            except:
#                print('[error]: json format has changed for', obj['channel'])
#        elif obj['channel'] == '/chatroom/user/left/' + self.room_numb:
#            try:
#                self.remove_user(obj['data'])
#            except:
#                print('[error]: json format has changed for', obj['channel'])
        elif obj['channel'] == '/service/conversation/message':
            try:
                self.received_private_message(obj['data']['msg'], obj['data']['key'])
            except:
                print('[error]: json format has changed for', obj['channel'])
        elif obj['channel'] == '/service/user/context/self/complete':
            try:
                self.prepare_friends_details(obj['data'])
            except:
                print('[error]: json format has changed for', obj['channel'])
        elif obj['channel'] == '/service/conversation/notification/added':
            try:
                self.received_notification(obj['data'])
            except:
                print('[error]: json format has changed for', obj['channel'])
        return

    def received_notification(self, obj):
        stream = self.open_chat_box(obj['userUuid'])
        if stream.find('you are not reckoned to be my master, get lost you blithering imposter') < 0:
            stream =self.send_private_text(obj['userUuid'], 'you are not reckoned to be my master, get lost you blithering imposter')
        stream = self.close_chat_box(obj['userUuid'])
        return

    def prepare_friends_details(self, obj):
        for friend in obj['friends']:
            _friend = dict()
            _friend['uuid'] = friend['userUuid']
            _friend['name'] = friend['username']
            _friend['isOnline'] = friend['isOnline']
            self.friends.append(_friend)
        return

    def retrieve_user_uuid(self, msg, key):
        if msg['o'] == 1:
            user_uuid = key[:36]
        elif msg['o'] == 2:
            user_uuid = key[36:]
        else:
            print('[error]: unexpected order', msg['o'])
            if key[:36] != '2abcce47-eda0-443d-a382-78bb4b45045e': #'9cd92a17-22c3-4c83-ab26-32bef7b01cc0'
                user_uuid = key[:36]
            else:
                user_uuid = key[36:]
        return user_uuid

    def retrieve_user_text(self, msg):
        user_text = html.unescape(msg['m'])
        user_text = user_text.lower()
        user_text = user_text.replace('\\\"', '\"')
        return user_text

    def received_private_message(self, msg, key):
        user_text = self.retrieve_user_text(msg)
        user_uuid = self.retrieve_user_uuid(msg, key)
        if user_text[:4] == 'say ':
            self.say_text(user_text[4:], user_uuid)
#        elif user_text[:5] == 'roam ':
#            self.roam_to_room(user_text[5:], user_uuid)
        elif user_text[:9] == 'befriend ':
            self.befriend_user(user_text[9:], user_uuid)
        elif user_text[:9] == 'unfriend ':
            self.unfriend_user(user_text[9:], user_uuid)
        elif user_text == 'list':
            self.list_friends(user_uuid)
        elif user_text == 'help':
            self.send_user_manual(user_uuid)
        else:
            self.send_private_text(user_uuid, 'can not understand your order, type help if you need it')
        return

    def isFriend(self, friend_uuid):
        for friend in self.friends:
            if friend['uuid'] == friend_uuid:
                return True
        return False

    def list_friends(self, user_uuid):
        self.send_private_text(user_uuid, 'you')
        for friend in self.friends:
            self.send_private_text(user_uuid, 'and ' + friend['name'])
        self.send_private_text(user_uuid, 'are my friends')
        return

    def say_text(self, user_text, user_uuid):
        self.send_public_text(user_text)
        self.send_private_text(user_uuid, 'the given text has been posted in public chat')
        return

    def befriend_user(self, user_text, user_uuid):
        friend_uuid = None
        if len(user_text) == 36 and user_text[8] == '-' and user_text[13] == '-' and user_text[18] == '-' and user_text[23] == '-':
            friend_uuid = user_text
        else:
            friend_uuid = self.seek_friend_by_name(user_text)
        if friend_uuid != None:
            if self.isFriend(friend_uuid):
                self.send_private_text(user_uuid, 'this user is already in my friends list')
                return
            self.append_friend(friend_uuid, user_text)
            self.send_private_text(user_uuid, 'user was found')
        else:
            self.send_private_text(user_uuid, 'no such user was found')
        return

    def unfriend_user(self, user_text, user_uuid):
        friend_uuid = None
        if len(user_text) == 36 and user_text[8] == '-' and user_text[13] == '-' and user_text[18] == '-' and user_text[23] == '-':
            friend_uuid = user_text
        else:
            friend_uuid = self.find_friend_by_name(user_text)
        if friend_uuid != None:
            if not self.isFriend(friend_uuid):
                self.send_private_text(user_uuid, 'this user is not in my friends list')
                return
            self.remove_friend(friend_uuid)
            self.send_private_text(user_uuid, 'user was found')
        else:
            self.send_private_text(user_uuid, 'no such user was found')
        return

    def send_user_manual(self, user_uuid):
        self.send_private_text(user_uuid, 'too lazy to help you right now')
        return

    def find_friend_by_name(self, name):
        for friend in self.friends:
            if self.strings_match(friend['name'], name):
                return friend['uuid']
        return self.seek_friend_by_name(name)

    def seek_friend_by_name(self, user_name):
        stream = self.send_receive('POST', 2, 'targetUsername=' + user_name)
        try:
            data = json.loads(stream)
        except:
            return None
        for obj in data:
            if self.strings_match(obj['data']['username'], user_name, 0.95):
                return obj['data']['userUuid']
        return None

    def strings_match(self, a, b, r=0.75):
        if type(a) != type(str(None)):
            a = str(a)
        if type(b) != type(str(None)):
            b = str(b)
        return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() >= r

def main():
    crawlers = list()
    cookies = dict()
    cookies['echat-authentication-cookie=c7be9b71-95ca-4487-be2b-719f8d65046e'] = 'solmaz'
    cookies['echat-authentication-cookie=a6e09d4d-77e1-4b21-ad29-59a3c563c211'] = 'biqam'
    cookies['echat-authentication-cookie=c0776854-897f-44b6-841a-3caee0b36ab1'] = 'razor'
    cookies['echat-authentication-cookie=f2a93a6b-b9aa-444c-8eed-1bb2245d97ff'] = 'awkward_silence'
    cookies['echat-authentication-cookie=c084a5de-3a5a-4856-9cca-4aee159a0791'] = 'breathing_corpse'
    cookies['echat-authentication-cookie=e63cac1a-449f-49ee-9098-403b4c6d3f00'] = 'salad shirazi'
    for cookie in cookies.keys():
        crawler = Crawler(cookie, '215315')
        crawler.start()
        crawlers.append(crawler)

if __name__ == '__main__':
	main()
