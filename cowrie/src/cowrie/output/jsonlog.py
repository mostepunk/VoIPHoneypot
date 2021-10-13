# Copyright (c) 2015 Michel Oosterhof <michel@oosterhof.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The names of the author(s) may not be used to endorse or promote
#    products derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHORS ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

from __future__ import absolute_import, division

import json
import os
import shutil
import datetime

import cowrie.core.output
import cowrie.python.logfile
from cowrie.core.config import CowrieConfig


class Output(cowrie.core.output.Output):

    """
    jsonlog output
    """
    def start(self):
        self.epoch_timestamp = CowrieConfig().getboolean('output_jsonlog', 'epoch_timestamp', fallback=False)
        fn = CowrieConfig().get('output_jsonlog', 'logfile')
        dirs = os.path.dirname(fn)
        base = os.path.basename(fn)
        self.outfile = cowrie.python.logfile.CowrieDailyLogFile(base, dirs, defaultMode=0o664)

    def stop(self):
        self.outfile.flush()

    def write(self, logentry):
        if self.epoch_timestamp:
            logentry['epoch'] = int(logentry['time'] * 1000000 / 1000)
        for i in list(logentry.keys()):
            # Remove twisted 15 legacy keys
            if i.startswith('log_') or i == 'time' or i == 'system':
                del logentry[i]
            if i == "new_session":
                logentry["session"] = logentry[i]
                del logentry[i]

        #  cowrie.client.fingerprint
        #  cowrie.client.size
        #  cowrie.client.var
        #  cowrie.client.version
        #  cowrie.command.failed
        #  cowrie.command.success
        #  cowrie.direct-tcpip.data
        #  cowrie.direct-tcpip.request
        #  cowrie.log.closed
        #  cowrie.login.failed
        #  cowrie.login.success
        #  cowrie.session.closed
        #  cowrie.session.connect
        #  cowrie.session.file_download
        #  cowrie.session.file_upload

        eventid = logentry.get("eventid")

        if eventid in ["cowrie.command.failed", "cowrie.command.success"]:
            logentry["eventid"] = "command_accept"
            logentry["command_input"] = logentry["input"]
            logentry["command_input_codec"] = "plain"

            if eventid == "cowrie.command.failed":
                logentry["command_output"] = logentry["message"]
                logentry["command_output_codec"] = "plain"

            del logentry["input"]
        elif eventid in ["cowrie.login.failed", "cowrie.login.success"]:
            logentry["eventid"] = "authorization"
            logentry["auth_status"] = True if eventid == "cowrie.login.success" else False
        elif eventid == "cowrie.session.closed":
            logentry["eventid"] = "disconnection"
            del logentry["duration"]
        elif eventid == "cowrie.session.connect":
            logentry["eventid"] = "connection"
        elif eventid == "cowrie.session.file_download":
            logentry["eventid"] = "file_download"
            logentry["file_sha256"] = logentry["shasum"]
            logentry["file_name"] = logentry["outfile"].split("/")[-1]
            del logentry["shasum"]

            logentry["file_path"] = logentry["outfile"]

            del logentry["outfile"]
        elif eventid == "cowrie.session.file_upload":
            logentry["eventid"] = "file_upload"
            logentry["file_sha256"] = logentry["shasum"]
            logentry["file_name"] = logentry["filename"]
            del logentry["shasum"]
            del logentry["filename"]

            logentry["file_path"] = logentry["outfile"]

            del logentry["outfile"]

        # elif eventid == "cowrie.command.input":
        #     logentry["eventid"] = "command_accept"
        #     logentry["command_input"] = logentry["input"]
        #     logentry["command_input_codec"] = "plain"
        #     del logentry["input"]
        else:
            # Skip other events
            return

        logentry["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            json.dump(logentry, self.outfile, separators=(',', ':'))
            self.outfile.write('\n')
            self.outfile.flush()
        except TypeError:
            print("jsonlog: Can't serialize: '" + repr(logentry) + "'")
