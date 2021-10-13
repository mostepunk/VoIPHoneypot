# Copyright (c) 2015 Michel Oosterhof <michel@oosterhof.net>
# All rights reserved.

"""
This module ...
"""

from __future__ import absolute_import, division

import getopt

from twisted.python import log

from cowrie.shell.command import HoneyPotCommand

commands = {}


class command_ulimit(HoneyPotCommand):

    """
    ulimit

    ulimit: usage: ulimit [-SHacdfilmnpqstuvx] [limit]
    """
    def call(self):
        # Parse options or display no files
        try:
            opts, args = getopt.getopt(self.args, 'SHacdfilmnpqstuvx')
        except getopt.GetoptError as err:
            self.errorWrite("-bash: ulimit: {}\n".format(err))
            self.write("ulimit: usage: ulimit [-SHacdfilmnpqstuvx] [limit]\n")
            return

        # Parse options
        for o, a in opts:
            if o in ('-c'):
                self.do_ulimit(key='core', value=a)
                return
            elif o in ('-a'):
                self.do_ulimit(key='all')
                return
        self.do_ulimit()

    def do_ulimit(self, key='core'):
        pass

    def exit(self):
        output, codec = self.get_output()
        realm = 'ulimit'
        log.msg(
            eventid='cowrie.command.success',
            realm=realm,
            input=f"{realm} {' '.join(self.args)}" if self.args else realm,
            command_output=output,
            command_output_codec=codec,
            format='INPUT (%(realm)s): %(input)s'
        )
        super(commands[realm], self).exit()


commands['ulimit'] = command_ulimit
