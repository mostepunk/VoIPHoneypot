from __future__ import absolute_import, division

from twisted.python import log

from cowrie.shell.command import HoneyPotCommand

commands = {}
"""
env: invalid option -- 'h'
Try `env --help' for more information.

Usage: env [OPTION]... [-] [NAME=VALUE]... [COMMAND [ARG]...]
Set each NAME to VALUE in the environment and run COMMAND.

  -i, --ignore-environment  start with an empty environment
  -0, --null           end each output line with 0 byte rather than newline
  -u, --unset=NAME     remove variable from the environment
      --help     display this help and exit
      --version  output version information and exit

A mere - implies -i.  If no COMMAND, print the resulting environment.

Report env bugs to bug-coreutils@gnu.org
GNU coreutils home page: <http://www.gnu.org/software/coreutils/>
General help using GNU software: <http://www.gnu.org/gethelp/>
For complete documentation, run: info coreutils 'env invocation'
"""


class command_env(HoneyPotCommand):
    def call(self):
        # This only show environ vars, not the shell vars. Need just to mimic real systems
        for i in list(self.protocol.environ.keys()):
            self.write('{0}={1}\n'.format(i, self.protocol.environ[i]))

    def exit(self):
        output, codec = self.get_output()
        realm = 'env'
        log.msg(
            eventid='cowrie.command.success',
            realm=realm,
            input=f"{realm} {' '.join(self.args)}" if self.args else realm,
            command_output=output,
            command_output_codec=codec,
            format='INPUT (%(realm)s): %(input)s'
        )
        super(commands[realm], self).exit()


commands['/usr/bin/env'] = command_env
commands['env'] = command_env
