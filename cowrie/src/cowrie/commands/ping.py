# Copyright (c) 2009 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

from __future__ import absolute_import, division

import getopt
import hashlib
import random
import re
import socket

from twisted.internet import reactor
from twisted.python import log

from cowrie.shell.command import HoneyPotCommand

commands = {}


class command_ping(HoneyPotCommand):
    def valid_ip(self, address):
        try:
            socket.inet_aton(address)
            return True
        except Exception:
            return False

    def start(self):
        self.host = None
        self.max = 0
        self.running = False

        try:
            optlist, args = getopt.gnu_getopt(self.args, "c:")
        except getopt.GetoptError as err:
            self.write('ping: %s\n' % (err, ))
            self.exit()
            return

        for opt in optlist:
            if opt[0] == '-c':
                try:
                    self.max = int(opt[1])
                except Exception:
                    self.max = 0
                if self.max <= 0:
                    self.write('ping: bad number of packets to transmit.\n')
                    self.exit()
                    return

        if len(args) == 0:
            for l in (
                    'Usage: ping [-LRUbdfnqrvVaA] [-c count] [-i interval] [-w deadline]',
                    '            [-p pattern] [-s packetsize] [-t ttl] [-I interface or address]',
                    '            [-M mtu discovery hint] [-S sndbuf]',
                    '            [ -T timestamp option ] [ -Q tos ] [hop1 ...] destination',
            ):
                self.write('{0}\n'.format(l))
            self.exit()
            return
        self.host = args[0].strip()

        if re.match('^[0-9.]+$', self.host):
            if self.valid_ip(self.host):
                self.ip = self.host
            else:
                self.write('ping: unknown host %s\n' % (self.host, ))
                self.exit()
        else:
            s = hashlib.md5((self.host).encode("utf-8")).hexdigest()
            self.ip = '.'.join([str(int(x, 16)) for x in (s[0:2], s[2:4], s[4:6], s[6:8])])

        self.running = True
        self.write('PING %s (%s) 56(84) bytes of data.\n' % (self.host, self.ip))
        self.scheduled = reactor.callLater(0.2, self.showreply)
        self.count = 0

    def showreply(self):
        ms = 40 + random.random() * 10
        self.write(
            '64 bytes from {} ({}): icmp_seq={} ttl=50 time={:.1f} ms\n'.format(self.host, self.ip, self.count + 1, ms)
        )
        self.count += 1
        if self.count == self.max:
            self.running = False
            self.write('\n')
            self.printstatistics()
            self.exit()
        else:
            self.scheduled = reactor.callLater(1, self.showreply)

    def printstatistics(self):
        self.write('--- %s ping statistics ---\n' % (self.host, ))
        self.write('%d packets transmitted, %d received, 0%% packet loss, time 907ms\n' % (self.count, self.count))
        self.write('rtt min/avg/max/mdev = 48.264/50.352/52.441/2.100 ms\n')

    def handle_CTRL_C(self):
        if self.running is False:
            return HoneyPotCommand.handle_CTRL_C(self)
        else:
            self.write('^C\n')
            self.scheduled.cancel()
            self.printstatistics()
            self.exit()

    def exit(self):
        output, codec = self.get_output()
        realm = 'ping'
        log.msg(
            eventid='cowrie.command.success',
            realm=realm,
            input=f"{realm} {' '.join(self.args)}" if self.args else realm,
            command_output=output,
            command_output_codec=codec,
            format='INPUT (%(realm)s): %(input)s'
        )
        super(commands[realm], self).exit()


commands['/bin/ping'] = command_ping
commands['ping'] = command_ping
