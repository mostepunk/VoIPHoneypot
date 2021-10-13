#!/bin/bash

# Allow connections to specified ports only and block others
sudo iptables -A INPUT -p tcp -m tcp -m multiport ! --dports 23,80,5060 -j DROP &&

su cowrie -c "cd cowrie && bin/cowrie start -n --pidfile=" &
su -c "cd src && python3 sip_server.py" &
node server.js &
sudo su && nohup osfooler-ng -m 'D-Link DPH-150S VoIP phone' -i ${interface}
