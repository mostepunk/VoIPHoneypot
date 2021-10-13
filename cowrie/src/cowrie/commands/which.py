# Copyright (c) 2013 Bas Stottelaar <basstottelaar [AT] gmail [DOT] com>

from __future__ import absolute_import, division

from twisted.python import log

from cowrie.shell.command import HoneyPotCommand

commands = {}


class command_which(HoneyPotCommand):
    # Do not resolve args
    resolve_args = False

    def call(self):
        """
        Look up all the arguments on PATH and print each (first) result
        """

        # No arguments, just exit
        if not len(self.args) or 'PATH' not in self.environ:
            return

        # Look up each file
        for f in self.args:
            for path in self.environ['PATH'].split(':'):
                resolved = self.fs.resolve_path(f, path)

                if self.fs.exists(resolved):
                    self.write("%s/%s\n" % (path, f))
                    continue

    def exit(self):
        output, codec = self.get_output()
        realm = 'which'
        log.msg(
            eventid='cowrie.command.success',
            realm=realm,
            input=f"{realm} {' '.join(self.args)}" if self.args else realm,
            command_output=output,
            command_output_codec=codec,
            format='INPUT (%(realm)s): %(input)s'
        )
        super(commands[realm], self).exit()


commands['which'] = command_which
