#!/bin/bash

nohup osfooler-ng -m "D-Link DPH-150S VoIP phone" -i eth0 &
python3 sip_server.py
