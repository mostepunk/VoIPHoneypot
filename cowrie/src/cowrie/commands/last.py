# Copyright (c) 2009 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

from __future__ import absolute_import, division

import time

from twisted.python import log

from cowrie.shell.command import HoneyPotCommand

commands = {}


class command_last(HoneyPotCommand):
    def call(self):
        line = list(self.args)
        while len(line):
            arg = line.pop(0)
            if not arg.startswith('-'):
                continue
            elif arg == '-n' and len(line) and line[0].isdigit():
                line.pop(0)

        self.write(
            '%-8s %-12s %-16s %s   still logged in\n' % (
                self.protocol.user.username, "pts/0", self.protocol.clientIP,
                time.strftime('%a %b %d %H:%M', time.localtime(self.protocol.logintime))
            )
        )

        self.write("\n")
        self.write(
            "wtmp begins %s\n" % time
            .strftime('%a %b %d %H:%M:%S %Y', time.localtime(self.protocol.logintime // (3600*24) * (3600*24) + 63))
        )

    def exit(self):
        output, codec = self.get_output()
        realm = 'last'
        log.msg(
            eventid='cowrie.command.success',
            realm=realm,
            input=f"{realm} {' '.join(self.args)}" if self.args else realm,
            command_output=output,
            command_output_codec=codec,
            format='INPUT (%(realm)s): %(input)s'
        )
        super(commands[realm], self).exit()


commands['/usr/bin/last'] = command_last
commands['last'] = command_last
