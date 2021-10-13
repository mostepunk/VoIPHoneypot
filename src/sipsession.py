from logger.logwrite import logger
import json

with open('config.json') as json_file:
    g_sipconfig = json.load(json_file)

class SipSession(object):
    """ Usually, a new SipSession instance is created when the SIP server
        receives an INVITE message
    """
    #   0           1               2               3
    NO_SESSION, SESSION_SETUP, ACTIVE_SESSION, SESSION_TEARDOWN = range(4)
    sipConnection = None

    def __init__(self, conInfo, rtpPort, inviteHeaders):
        if not SipSession.sipConnection:
            logger.error("SIP connection class variable not set")

            # Store incoming information of the remote host
            self.__inviteHeaders = inviteHeaders
            self.__state = SipSession.SESSION_SETUP # 1
            self.__remoteAddress = conInfo[0]
            self.__remoteSipPort = conInfo[1]
            self.__remoteRtpPort = rtpPort

            # Generate static values for SIP messages
            global g_sipconfig
            self.__sipTo = inviteHeaders['From']
            self.__sipFrom = "{0} <sip:{0}@{1}>".format(g_sipconfig['user'],
                                                        g_sipconfig['ip'])
            self.__sipVia = "SIP/2.0/UDP {}:{}".format(g_sipconfig['ip'],
                                                       g_sipconfig['port'])

            # Create RTP stream instance and pass address and port of listening
            # remote RTP host
            # Заготовка для голосового соединения
            # self.__rtpStream = RtpUdpStream(self.__remoteAddress,
                                            # self.__remoteRtpPort)

            # Send 180 Ringing to make honeypot appear more human-like
            # TODO Delay between 180 and 200
            msgLines = []
            msgLines.append("SIP/2.0 180 Ringing")
            msgLines.append("Via: " + self.__sipVia)
            msgLines.append("Max-Forwards: 70")
            msgLines.append("To: " + self.__sipTo)
            msgLines.append("From: " + self.__sipFrom)
            msgLines.append("Call-ID: {}".format(self.__inviteHeaders['Call-ID']))
            msgLines.append("CSeq: 1 INVITE")
            msgLines.append("Contact: " + self.__sipFrom)
            msgLines.append("User-Agent: " + g_sipconfig['useragent'])
            self.msg_ringing = '\r\n'.join(msgLines)
            # SipSession.sipConnection.send('\n'.join(msgLines))

            # Send our RTP port to the remote host as a 200 OK response to the
            # remote host's INVITE request
            # logger.debug("getsockname: {}".format(self.__rtpStream.getsockname()))
            # localRtpPort = self.__rtpStream.getsockname()[1]
            localRtpPort = g_sipconfig["port"]

            msgLines = []
            msgLines.append("SIP/2.0 200 OK")
            msgLines.append("Via: " + self.__sipVia)
            msgLines.append("Max-Forwards: 70")
            msgLines.append("To: " + self.__sipTo)
            msgLines.append("From: " + self.__sipFrom)
            msgLines.append("Call-ID: {}".format(self.__inviteHeaders['Call-ID']))
            msgLines.append("CSeq: 1 INVITE")
            msgLines.append("Contact: " + self.__sipFrom)
            msgLines.append("User-Agent: " + g_sipconfig['useragent'])
            msgLines.append("Content-Type: application/sdp")
            msgLines.append("\nv=0")
            msgLines.append("o=... 0 0 IN IP4 localhost")
            msgLines.append("t=0 0")
            msgLines.append("m=audio {} RTP/AVP 0".format(localRtpPort))
            self.msg_ok = '\r\n'.join(msgLines)
            # SipSession.sipConnection.send('\n'.join(msgLines))

    def handle_ACK(self, headers, body):
        if self.__state == SipSession.SESSION_SETUP:
            logger.debug(
                "Waiting for ACK after INVITE -> got ACK -> active session")
            logger.info("Connection accepted (session {})".format(
                self.__inviteHeaders['Call-ID']))

                # Set current state to active (ready for multimedia stream)
            self.__state = SipSession.ACTIVE_SESSION

    def handle_BYE(self, headers, body=None):
        global g_sipconfig

        # Only close down RTP stream if session is active
        if self.__state == SipSession.ACTIVE_SESSION:
            # self.__rtpStream.close()
            pass

        # A BYE ends the session immediately
        self.__state = SipSession.NO_SESSION

        # Send OK response to other client
        msgLines = []
        msgLines.append("SIP/2.0 200 OK")
        msgLines.append("Via: " + self.__sipVia)
        msgLines.append("Max-Forwards: 70")
        msgLines.append("To: " + self.__sipTo)
        msgLines.append("From: " + self.__sipFrom)
        msgLines.append("Call-ID: {}".format(self.__inviteHeaders['Call-ID']))
        msgLines.append("CSeq: 1 BYE")
        msgLines.append("Contact: " + self.__sipFrom)
        msgLines.append("User-Agent: " + g_sipconfig['useragent'])
        self.msg_bye = '\r\n'.join(msgLines)
        # SipSession.sipConnection.send('\n'.join(msgLines))

