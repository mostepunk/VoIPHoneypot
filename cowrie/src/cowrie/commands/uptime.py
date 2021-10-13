# Copyright (c) 2009 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

from __future__ import absolute_import, division

import time

from twisted.python import log

from cowrie.core import utils
from cowrie.shell.command import HoneyPotCommand

commands = {}


class command_uptime(HoneyPotCommand):
    def call(self):
        self.write(
            '%s  up %s,  1 user,  load average: 0.00, 0.00, 0.00\n' %
            (time.strftime('%H:%M:%S'), utils.uptime(self.protocol.uptime()))
        )

    def exit(self):
        output, codec = self.get_output()
        realm = 'uptime'
        log.msg(
            eventid='cowrie.command.success',
            realm=realm,
            input=f"{realm} {' '.join(self.args)}" if self.args else realm,
            command_output=output,
            command_output_codec=codec,
            format='INPUT (%(realm)s): %(input)s'
        )
        super(commands[realm], self).exit()


commands['/usr/bin/uptime'] = command_uptime
commands['uptime'] = command_uptime
