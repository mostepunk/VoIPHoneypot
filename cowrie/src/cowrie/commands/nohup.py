# -*- coding: utf-8 -*-
# Copyright (c) 2014 Peter Reuterås <peter@reuteras.com>
# See the COPYRIGHT file for more information

from __future__ import absolute_import, division

from twisted.python import log

from cowrie.shell.command import HoneyPotCommand

commands = {}


class command_nohup(HoneyPotCommand):
    def call(self):
        if not len(self.args):
            self.write('nohup: missing operand\n')
            self.write('Try `nohup --help\' for more information.\n')
            return
        path = self.fs.resolve_path("nohup.out", self.protocol.cwd)
        if self.fs.exists(path):
            return
        self.fs.mkfile(path, 0, 0, 0, 33188)
        self.write("nohup: ignoring input and appending output to 'nohup.out'\n")

    def exit(self):
        output, codec = self.get_output()
        realm = 'nohup'
        log.msg(
            eventid='cowrie.command.success',
            realm=realm,
            input=f"{realm} {' '.join(self.args)}" if self.args else realm,
            command_output=output,
            command_output_codec=codec,
            format='INPUT (%(realm)s): %(input)s'
        )
        super(commands[realm], self).exit()


commands['/usr/bin/nohup'] = command_nohup
commands['nohup'] = command_nohup
