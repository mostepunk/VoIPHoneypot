
class RtpUdpStream:
    """RTP stream that can send data and writes the whole conversation to a
    file"""
    def __init__(self, name, call, session, local_address, local_port, remote_address, remote_port, bistream_enabled=False, pcap=None):
        logger.debug("{} __init__".format(self))

        self._call = call
        self._name = name
        self._pcap = pcap
        self._session = session

        # Bind to free random port for incoming RTP traffic
        self.bind(local_address, local_port)
        self.connect(remote_address, remote_port)

        # The address and port of the remote host
        self.remote.host = remote_address
        self.remote.port = remote_port

        self._bistream = []
        self._bistream_enabled = bistream_enabled

        # Send byte buffer
        self.__sendBuffer = b''

        logger.info("Created RTP channel on ports :{} <-> :{}".format(
            self.local.port, self.remote.port))

    def close(self):
        logger.debug("{} close".format(self))
        logger.debug("Closing stream dump (in)")
        connection.close(self)

        if len(self._bistream) == 0:
            return

        now = datetime.datetime.now()
        dirname = "%04i-%02i-%02i" % (now.year, now.month, now.day)
        bistream_path = os.path.join('bistreams', dirname)
        if not os.path.exists(bistream_path):
            os.makedirs(bistream_path)

        fp = tempfile.NamedTemporaryFile(
            delete=False,
            prefix="SipCall-{local_port}-{remote_host}:{remote_port}-".format(local_port=self.local.port, remote_host=self.remote.host, remote_port=self.remote.port),
            dir=bistream_path
        )
        fp.write(b"stream = ")
        fp.write(str(self._bistream).encode())
        fp.close()

    def handle_established(self):
        logger.debug("{} handle_established".format(self))

    def handle_timeout_idle(self):
        logger.debug("{} handle_timeout_idle".format(self))
        self.close()
        return False

    def handle_timeout_sustain(self):
        logger.debug("{} handle_timeout_sustain".format(self))
        return False

    def handle_io_in(self, data):
        logger.debug("{} handle_io_in".format(self))
        # logger.debug("Incoming RTP data (length {})".format(len(data)))

        if self._bistream_enabled:
            self._bistream.append(("in", data))
        if self._pcap:
            self._pcap.write(src_port=self.remote.port, dst_port=self.local.port, data=data)

        return len(data)

    def handle_io_out(self):
        logger.info("{} handle_io_out".format(self))

    def handle_disconnect(self):
        logger.info("{} handle_disconnect".format(self))
        self._call.event_stream_closed(self._name)
        self._pcap.close()
        return False

    def handle_error(self, err):
        self._call.event_stream_closed(self._name)

