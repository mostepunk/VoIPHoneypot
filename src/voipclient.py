import json
import uuid
import hashlib
from twisted.protocols.sip import Base

from sipsession import SipSession
from logger.logwrite import logger


# TODO [ ] cleanup __sessions after disconnection
class VoipClient(Base):
    __sessions = {}
    json_list = []
    local_address = {}
    proto = ''
    addr = ''
    with open('config.json', 'r') as json_file:
        g_sipconfig = json.load(json_file)

    def get_headers(self, message):
        """ Parse message:
                INVITE sip:100@localhost SIP/2.0
                Via: SIP/2.0/UDP 127.0.0.1:5060;branch=z9hG4bK87asdks7
                From: socketHelper
                    ...
                v=0
                    ...
                m=audio 30123 RTP/AVP 0
            ---------
            into dict:
                {'INVITE sip' : '100@localhost SIP/2.0',
                    'Via'     : 'SIP/2.0/UDP 127.0.0.1:5060;branch=z9hG4bK87asdks7',
                    'From'    : 'socketHelper',
                    'v'       : '0',
                    'm'       : 'audio 30123 RTP/AVP 0'}
        """
        final_list = []
        my_dict = {}
        if message[0].endswith('\r\n') or message[0].endswith('\r\n\r'):
            findall = message[0].split('\r\n')
            logger.info(f'findall[rn] - {findall}')

        elif message[0].endswith('\n\n'):
            findall = message[0].split('\n\n')
            logger.info(f'findall[nn] - {findall}')

        else:
            findall = None

        if findall:
            for f in findall:
                find_more = f.split('\n')
                if find_more:
                    final_list.append(find_more)
                    # logger.info(f'find_more - {find_more}')

            for list_in_list in final_list:
                for item_list in  list_in_list:
                    if ':' in item_list:
                        spl = item_list.split(':', 1)
                        # logger.info(f'I found something : {spl}')

                    elif '=' in item_list:
                        spl = item_list.split('=')
                        # logger.info(f'I found something = {spl}')
                    else:
                        spl = None
                        # logger.info(f'I don\'t found anything in {item_list}')


                    if spl:
                        my_dict[spl[0].strip()] = spl[1].strip()
                    else:
                        continue

            logger.info('Prepare dict for headers - \n%s'% my_dict)
        return my_dict

    def worker(self, message):
        list_mes = [message]
        headers = self.get_headers(list_mes)

        if message.startswith('OPTIONS'):
            data = self.sip_OPTIONS(headers, message)

        elif message.startswith('INVITE'):
            data = self.sip_INVITE(headers, message)

        elif message.startswith('CANCEL'):
            data = self.sip_CANCEL(headers, message)

        elif message.startswith('BYE'):
            data = self.sip_BYE(headers, message)

        elif message.startswith('ACK'):
            self.sip_ACK(headers, message)
            data = None

        elif message.startswith('REGISTER'):
            self.sip_REGISTER(headers, message)
            data = None

        elif message.startswith('RESPONSE'):
            self.sip_RESPONSE(headers, message)
            data = None

        elif message.startswith('GET'):
            data = ''

        else:
            logger.info('ELSE was delivered \n%s'% message)
            # data = b"8====D - - - --- -\r\n"
            # data = "...................../´¯¯/)\r\n...................,/¯.../\r\n.................../..../\r\n .............../´¯/'..'/´¯¯`·¸\r\n.........../'/.../..../....../¨¯\ \r\n..........('(....´...´... ¯~/'..')\r\n...........\..............'...../\r\n............\....\.........._.·´\r\n.............\..............(\r\n..............\..............\ \r\n"
            data = ''
            obj = {
                "eventid" : "command_accept",
                "command_input": message,
                "command_output": str(data),
                "command_input_codec": "bytes",
                "command_output_codec": "plain",
            }
            self.report(obj)

        final_data = {}
        final_data['data'] = [data]
        final_data['reports'] = []

        for i in self.json_list: final_data['reports'].append(i)
        self.json_list.clear()
        return final_data

    def report(self, j_dict):
        self.json_list.append(j_dict)

    # [v] check
    def sip_OPTIONS(self, headers, incom_msg):
        """ Construct OPTIONS response
        """
        logger.info("Received OPTIONS")
        msgLines = []

        branch_line = headers['Via'].split(';')
        for l in branch_line:
            if l.startswith('branch='):
                branch = l.strip('\r\n')

        tag_line = headers['From'].split(';') #[1].strip('\r\n')
        for l in tag_line:
            if l.startswith('tag='):
                tag = l.strip('\r\n')

        msgLines.append("SIP/2.0 200 OK")
        if branch:
            msgLines.append(
                "Via: SIP/2.0/{0} {1}:{2};rport={2};{3}"
                .format(self.proto,
                        self.addr[0],
                        self.addr[1],
                        branch))
        else:
            msgLines.append(
                "Via: SIP/2.0/{0} {1}:{2};rport={2}"
                .format(self.proto,
                        self.addr[0],
                        self.addr[1],
                        ))

        msgLines.append("To: " + headers['From'])
        if tag:
            msgLines.append(
                "From: {0} <sip:{0}@{1}> {2}"
                .format(self.g_sipconfig['user'],
                        self.local_address['ip'],
                        tag))
        else:
            msgLines.append(
                "From: {0} <sip:{0}@{1}>"
                .format(self.g_sipconfig['user'],
                        self.local_address['ip']))

        msgLines.append("Call-ID: " + headers['Call-ID'])
        msgLines.append("CSeq: " + headers['CSeq'])
        msgLines.append("Contact: {0} <sip:{0}@{1}>".format(self.g_sipconfig['user'],
                                                            self.local_address['ip']))
        msgLines.append("Supported: 100rel, replaces, timer")
        msgLines.append("Allow: INVITE, ACK, OPTIONS, BYE, CANCEL, REFER, NOTIFY, INFO, PRACK, UPDATE, MESSAGE")
        msgLines.append("Accept: application/sdp, message/sipfrag, application/dtmf-relay")
        msgLines.append("Accept-Language: en")
        msgLines.append("\r\n")

        options_headers = '\r\n'.join(msgLines)
        logger.info('Options headers: %s'% options_headers)

        obj = {
            "eventid" : "command_accept",
            "command_input": incom_msg,
            "command_output": options_headers,
            "command_input_codec": "bytes",
            "command_output_codec": "bytes",
        }
        self.report(obj)

        return options_headers.encode()

    # [v] check
    def sip_INVITE(self, headers, incom_msg):
        """ answer on INVITE requests
        """
        answer = self.__check_invite(headers, incom_msg)
        if isinstance(answer, str):
            obj = {
                "eventid" : "command_accept",
                "command_input": incom_msg,
                "command_input_codec": "bytes",
                "command_output": answer,
                "command_output_codec": "bytes",
            }
            self.report(obj)
            answer.encode()

        elif isinstance(answer, tuple):
            for an in answer:
                obj = {
                    "eventid" : "command_accept",
                    "command_input": incom_msg,
                    "command_input_codec": "bytes",
                    "command_output": an,
                    "command_output_codec": "bytes",
                }
                self.report(obj)
        return answer

    def bad_answer(self, incom_msg, headers, code):
        try:
            answer = self.g_sipconfig['bad_answers'][str(code)]
        except KeyError:
            logger.error('Bad code was given - %s'%code)
            answer = self.g_sipconfig['bad_answers']['400']

        answLines = []
        answLines.append("SIP/2.0 " + answer)
        answLines.append(
            "Via: SIP/2.0/{} {}:{}"
            .format(self.proto,
                    self.local_address['ip'],
                    self.local_address['port'])
        )
        answLines.append("To: " + headers['From'])
        answLines.append(
            "From: {0} <sip:{0}@{1}>"
            .format(self.g_sipconfig['user'],
                    self.local_address['ip'])
        )
        answLines.append("Call-ID: " + headers['Call-ID'])
        answLines.append("CSeq: " + headers['CSeq'])
        answLines.append(
            "Contact: {0} <sip:{0}@{1}>"
            .format(self.g_sipconfig['user'],
                    self.local_address['ip'])
        )
        answLines.append("\r\n")
        ret_lines = '\r\n'.join(answLines)

        obj = {
            "eventid" : "command_accept",
            "command_input": incom_msg,
            "command_output": ret_lines,
            "command_input_codec": "bytes",
            "command_output_codec": "bytes",
        }
        self.report(obj)
        return ret_lines

    # [v] check
    def sip_ACK(self, headers, incom_msg):
        """ Команда подтверждения, после нее начинается rtp соединение """
        logger.info("Received ACK")

        try:
            s = self.__sessions[headers["Call-ID"]]
        except KeyError:
            logger.error("Given Call-ID does not belong to a session: exit")
            # send  481: b"Call/Transaction Does Not Exist",
            return self.bad_answer(headers, incom_msg, 481)

        # Handle incoming ACKs depending on current state
        # s.handle_ACK(headers, body)
        obj = {
            "eventid" : "command_accept",
            "command_input": incom_msg,
            "command_output": '',
            "command_input_codec": "bytes",
            "command_output_codec": "plain",
        }
        self.report(obj)

    # [v] check
    def sip_BYE(self, headers, incom_msg):
        logger.info("Received BYE")

        # Get SIP session for given Call-ID
        try:
            s = self.__sessions[headers["Call-ID"]]
        except KeyError:
            logger.error("Given Call-ID does not belong to a session: exit")
            # send  481: "Call/Transaction Does Not Exist",
            return self.bad_answer(incom_msg, headers, 481)

        # Handle incoming BYE request depending on current state
        s.handle_BYE(headers)
        obj = {
            "eventid" : "command_accept",
            "command_input": incom_msg,
            "command_output": s.msg_bye,
            "command_input_codec": "bytes",
            "command_output_codec": "plain",
        }
        self.report(obj)
        return s.msg_bye

    # [v] check
    def sip_CANCEL(self, headers, incom_msg):
        logger.info("Received CANCEL")

        # Get Call-Id and check if there's already a SipSession
        callId = headers['Call-ID']

        # Get CSeq to find out which request to cancel
        cseq = headers['CSeq'].split(' ')
        cseqNumber = cseq[0]
        cseqMethod = cseq[1]

        if cseqMethod == "INVITE" or cseqMethod == "ACK":
            # Find SipSession and delete it
            if callId not in self.__sessions:
                logger.info(
                    "CANCEL request does not match any existing SIP session")
                # 403: "Forbidden"
                return self.bad_answer(incom_msg, headers, 404)

            # No RTP connection has been made yet so deleting the session
            # instance is sufficient
            del self.__sessions[callId]

        # Construct CANCEL response
        msgLines = []
        msgLines.append("SIP/2.0 200 OK")
        msgLines.append("Via: SIP/2.0/{} {}:{}".format(self.proto,
                                                       self.local_address['ip'],
                                                       self.local_address['port']))
        msgLines.append("To: " + headers['From'])
        msgLines.append("From: {0} <sip:{0}@{1}>".format(self.g_sipconfig['user'],
                                                         self.local_address['ip']))
        msgLines.append("Call-ID: " + headers['Call-ID'])
        msgLines.append("CSeq: " + headers['CSeq'])
        msgLines.append("Contact: {0} <sip:{0}@{1}>".format(self.g_sipconfig['user'],
                                                            self.local_address['ip']))

        ret_lines = '\r\n'.join(msgLines)

        obj = {
            "eventid" : "command_accept",
            "command_input": incom_msg,
            "command_output": ret_lines,
            "command_input_codec": "bytes",
            "command_output_codec": "bytes",
        }
        self.report(obj)
        return ret_lines

    # [v] check
    def sip_REGISTER(self, headers, incom_msg):
        logger.info("Received REGISTER")
        obj = {
            "eventid" : "command_accept",
            "command_input": incom_msg,
            "command_output": '',
            "command_input_codec": "bytes",
            "command_output_codec": "plain",
        }
        self.report(obj)

    # [v] check
    def sip_RESPONSE(self, headers, incom_msg):
        logger.info("Received a response")
        obj = {
            "eventid" : "command_accept",
            "command_input": incom_msg,
            "command_output": '',
            "command_input_codec": "bytes",
            "command_output_codec": "plain",
        }
        self.report(obj)

    def __check_invite(self, headers, message):
        def get_hash(s):
            return hashlib.md5(s.encode('utf-8')).hexdigest()

        nonce = get_hash(self.g_sipconfig['secret'])
        opaqueue = get_hash(str(uuid.uuid1()))

        if "Authorization" not in headers:
            # Send 401 Unauthorized response
            msgLines = []
            msgLines.append('SIP/2.0 ' + '401 Unauthorized')
            msgLines.append("Via: SIP/2.0/{} {}:{}".format(
                self.proto, self.local_address['ip'], self.local_address['port']))

            msgLines.append("To: " + headers['From'])
            msgLines.append("From: {0} <sip:{0}@{1}>".format(
                self.g_sipconfig['user'], self.local_address['ip']))

            msgLines.append("Call-ID: " + headers['Call-ID'])
            msgLines.append("CSeq: " + headers['CSeq'])
            msgLines.append("Contact: {0} <sip:{0}@{1}>".format(self.g_sipconfig['user'],
                                                                self.local_address['ip']))
            msgLines.append(
                'WWW-Authenticate: Digest ' +
                'realm="{}@{}",'.format(self.g_sipconfig['user'],
                                        self.local_address['ip']) +
                'nonce="{}",'.format(nonce) +
                'opaque="{}"'.format(opaqueue)
            )
            msgLines.append('\r\n')
            invite_headers = '\r\n'.join(msgLines)
            logger.info('Invite headers: %s'% invite_headers)
            return invite_headers

        else:
            auth_obj = {
                'eventid': 'authorization'
            }

            authMethod, authLine = headers['Authorization'].split(' ', 1)

            if authMethod != 'Digest':
                logger.error("Authorization is not Digest")
                auth_obj['auth_status'] = False
                self.report(auth_obj)
                return self.bad_answer(message, headers, 400)

            # Get Authorization header parts (a="a", b="b", c="c", ...) and put
            # them in a dictionary for easy lookup
            authLineParts = [x.strip(' \t\r\n') for x in authLine.split(',')]
            authLineDict = {}

            for x in authLineParts:
                parts = x.split('=')
                authLineDict[parts[0]] = parts[1].strip(' \n\r\t"\'')

            auth_obj['username'] = authLineDict['username']
            auth_obj['password'] = ''
            auth_obj['auth_status'] = True

            realm = "{}@{}".format(self.g_sipconfig['user'], self.local_address['ip'])
            uri = "sip:" + realm

            a1 = get_hash(
                "{}:{}:{}"
                .format(self.g_sipconfig['user'], realm, self.g_sipconfig['secret'])
            )
            a2 = get_hash("INVITE:{}".format(uri))

            expected = get_hash("{}:{}:{}".format(a1, nonce, a2))

            if expected != authLineDict['response']:
                logger.info(
                    f"expected - {expected} authLineDict - {authLineDict['response']}")
                logger.error("Authorization failed")
                auth_obj['auth_status'] = False
                self.report(auth_obj)

                # BAD_REQUEST: '400 Bad request',
                return self.bad_answer(message, headers, 400)

            logger.info(
                "Authorisation methods: expected - %s, authLineDict - %s"
                %(expected, authLineDict)
                )

            # 'm': 'audio 30123 RTP/AVP 0'
            mediaDescriptionParts = headers['m'].split(' ')
            rtpPort = mediaDescriptionParts[1]
            callId = headers["Call-ID"]

            if callId in self.__sessions:
                logger.info(
                    "SIP session with Call-ID {} already exists"
                    .format(callId)
                )
                auth_obj['auth_status'] = False
                self.report(auth_obj)

                # FORBIDDEN: '403 Forbidden',
                return self.bad_answer(message, headers, 403)

            # Establish a new SIP session
            newSession = SipSession(
                (self.addr[0], self.addr[1]), rtpPort, headers)

            # Store session object in sessions dictionary
            self.__sessions[callId] = newSession
            self.report(auth_obj)
            return (newSession.msg_ringing, newSession.msg_ok)

