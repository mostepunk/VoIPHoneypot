import datetime
import random
from OpenSSL import crypto

key = crypto.PKey()
key.generate_key(crypto.TYPE_RSA, 2048)
cert = crypto.X509()
cert.get_subject().C = "CN"
cert.get_subject().CN = "tplinkap.net"
cert.set_serial_number(random.randint(1, 999))
cert.set_notBefore(datetime.datetime.strptime('2020-07-08T21:00:12', "%Y-%m-%dT%H:%M:%S").strftime("%Y%m%d%H%M%SZ").encode())
cert.set_notAfter(datetime.datetime.strptime('2025-07-07T21:00:12', "%Y-%m-%dT%H:%M:%S").strftime("%Y%m%d%H%M%SZ").encode())
cert.set_issuer(cert.get_subject())
cert.set_pubkey(key)
cert.sign(key, 'sha384')
# cert.sign(key, 'sha256')

with open("certrequest.crt", "wb") as file:
    file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

with open("privatekey.pem", "wb") as file:
    file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
