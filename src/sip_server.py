from twisted.internet import reactor, protocol, endpoints
from twisted.internet.protocol import DatagramProtocol
from twisted.protocols.sip import Base, Request
from twisted.web import server

import asyncio
import json
import uuid
import time
import threading
from datetime import datetime
from dateutil.relativedelta import relativedelta

from logger.logwrite import OutputWriter, logger, OUTPUT_PLUGINS
from voipclient import VoipClient
from http_server import HTTPHandler

MINUTES_LEFT = 10
TIME_SLEEP = 30

with open('config.json', 'r') as json_file:
    g_sipconfig = json.load(json_file)


class TCPServer(protocol.Protocol):
    server_settings = {}
    def send(self, send_data):
        if send_data:
            if isinstance(send_data, str):
                send_data = send_data.encode()

            self.transport.write(send_data)

    def connectionMade(self):
        self.server_settings['ip'] = self.transport.getHost().host
        self.server_settings['port'] = self.transport.getHost().port
        logger.info('Connected to %s'%self.transport.getPeer().host)
        self.session = str(uuid.uuid1())
        obj = {
            'eventid' : 'connection'
        }
        self.report(obj)

    def connectionLost(self, reason):
        logger.info('Disconnected of %s'%self.transport.getPeer().host)
        obj = {
            'eventid' : 'disconnection'
        }
        self.report(obj)

    def dataReceived(self, incom_data):
        self.server_settings['ip'] = self.transport.getHost().host
        self.server_settings['port'] = self.transport.getHost().port

        v_client = VoipClient()
        v_client.addr = (self.transport.getPeer().host, self.transport.getPeer().port)
        v_client.local_address['ip'] = self.server_settings['ip']
        v_client.local_address['port'] = self.server_settings['port']
        v_client.proto = 'TCP'

        logger.info(f'=== New data arrived from addr:{v_client.addr[0]} data: \n{incom_data}')
        try:
            data_string = incom_data.decode()
            worker_data = v_client.worker(data_string)

            # worker_data = {
            #     'data': [
            #           b'SIP/2.0...',
            #           b'....'
            #             ],
            #     'reports': [
            #         {'eventid': 'command_accept', ...},
            #         {'eventid': 'authorization',  ...}
            #                ]}

            if worker_data:
                if isinstance(worker_data, dict):
                    for data in worker_data['reports']:
                        self.report(data)

                    for data in worker_data['data']:
                        self.send(data)

                else: # TODO raise error
                    # self.send(worker_data, addr)
                    pass

        except UnicodeDecodeError:
            logger.info('Can\'t decode string \n%s\n'% incom_data)
            obj = {
                'eventid': 'command_accept',
                'command_input': str(incom_data),
                'command_output': '',
                'command_input_codec': 'bytes',
                'command_output_codec': 'plain'
            }
            self.report(obj)

    def report(self, obj):
        """ Constant parameters for json
        """
        obj['timestamp'] = datetime.utcnow().isoformat()
        obj['session'] = self.session
        obj['type'] = 'd_link_dph150s'
        obj['protocol'] = 'tcp'
        obj['dest_ip'] = self.server_settings['ip']
        obj['dest_port'] = self.server_settings['port']
        obj['src_ip'] = self.transport.getPeer().host
        obj['src_port'] = self.transport.getPeer().port
        # logger.debug("Placing {} on log_q".format(obj))
        logger.write(obj)

class UDPServer(DatagramProtocol):
    sessions = {}
    is_checking = True
    server_settings = {}

    def check_conection(self):
        """ If IP address didn't send any pacage for a 5 min
            set eventid disconnection
            If the same IP will connect after 5 min
            it will be new session
        """
        def delete_from_dict(del_list):
            for address in del_list:
                logger.info(
                    'delete udp session - %s: %s'
                    %(address, self.sessions[address])
                )
                del self.sessions[address]

        while self.is_checking:
            list_to_delete = []

            for ip_address in self.sessions:
                start = self.sessions[ip_address]['datetime']

                if isinstance(start, str):
                    start = datetime.fromisoformat(start)

                # get positive minutes from datetime
                minutes = abs(relativedelta(start, datetime.utcnow()).minutes)
                logger.info(f'{ip_address}: Minutes left - {minutes}')

                if minutes > int(MINUTES_LEFT):
                    list_to_delete.append(ip_address)   # delete from self.sessions

                    obj = {
                        'eventid':'disconnection',
                        'src_ip': ip_address,
                        'src_port': self.sessions[ip_address]['port']
                    }
                    self.report(obj, self.sessions[ip_address]['session'])

            if list_to_delete:
                delete_from_dict(list_to_delete)

            if self.sessions:
                logger.info(
                    '%s Current UDP sessions:\n%s'
                    %(len(self.sessions), self.sessions)
                )
            time.sleep(int(TIME_SLEEP))

    def get_session(self):
        """ Generate unique session id uuid
            generate key pair in self.session_addr
                IP:uuid
            After 5 min afer last action
            thread check_connection will delete it
        """
        ip_address = self.addr[0]

        if ip_address not in self.sessions:
            session = str(uuid.uuid1())
            logger.info('NEW IP -%s SESSION - %s'%(ip_address, session))

            obj = {
                'eventid':'connection'
                }
            self.sessions[ip_address] = {
                'session': session,
                'datetime': datetime.utcnow(),
                'port' : self.addr[1]
                }
            self.report(obj, session)

        else:
            session = self.sessions[ip_address]['session']
            self.sessions[ip_address]['datetime'] = datetime.utcnow()

        return session

    def report(self, obj, session=None):
        """ Constant parameters for json
        """
        if not session:
            session = self.get_session()

        obj['timestamp'] = datetime.utcnow().isoformat()
        obj['session'] = session
        obj['type'] = 'd_link_dph150s'
        obj['protocol'] = 'udp'
        obj['dest_ip'] = self.server_settings['ip']
        obj['dest_port'] = self.server_settings['port']

        if 'src_ip' and 'src_port' not in obj:
            obj['src_ip'] = self.addr[0]
            obj['src_port'] = self.addr[1]

        logger.debug("Placing {} on log_q".format(obj))
        logger.write(obj)

    def datagramReceived(self, incom_data, addr):
        """ Start working with incoming data """
        # addr:('10.0.8.33', 36466)
        self.addr = addr

        v_client = VoipClient()
        v_client.addr = addr
        v_client.local_address['ip'] = self.server_settings['ip']
        v_client.local_address['port'] = self.server_settings['port']
        v_client.proto = 'UDP'

        logger.info(
            '=== New data arrived from addr:{} data: \n{}'
            .format(addr, incom_data)
        )
        try:
            data_string = incom_data.decode()
            worker_data = v_client.worker(data_string)

            # worker_data = {
            #     'data': [
            #           b'SIP/2.0...',
            #           b'....'
            #             ],
            #     'reports': [
            #         {'eventid': 'command_accept', ...},
            #         {'eventid': 'authorization',  ...}
            #                ]}

            if worker_data:
                if isinstance(worker_data, dict):
                    for data in worker_data['reports']:
                        self.report(data)

                    for data in worker_data['data']:
                        self.send(data, addr)

                else: # TODO raise error
                    pass

        except UnicodeDecodeError:
            logger.info('Can\'t decode string \n%s\n'% incom_data)
            obj = {
                'eventid': 'command_accept',
                'command_input': str(incom_data),
                'command_output': '',
                'command_input_codec': 'bytes',
                'command_output_codec': 'plain'
            }
            self.report(obj)

    def send(self, data, addr):
        """ Send answer to socket """
        if data:
            if isinstance(data, str):
                data = data.encode()

            self.transport.write(data, addr)

    def startProtocol(self):
        """ this method calls when programm start"""
        self.server_settings['ip'] = self.transport.getHost().host
        self.server_settings['port'] = self.transport.getHost().port

        self.output_writer = OutputWriter()
        self.isdisconnected = threading.Thread(target=self.check_conection)
        self.output_writer.start()
        self.isdisconnected.start()

    def stopProtocol(self):
        """ this method calls when programm finished"""
        if self.output_writer:
            self.output_writer.stop()

        if self.isdisconnected:
            self.is_checking = False

def main():
    logger.info("Configuration loaded with {} as output plugins".format(OUTPUT_PLUGINS))

    factory = protocol.ServerFactory()
    factory.protocol = TCPServer

    reactor.listenTCP(5060, factory)
    reactor.listenUDP(5060, UDPServer())
    reactor.run()

if __name__ == '__main__':
    main()
