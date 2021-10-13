import logging
import threading
import queue as Queue

OUTPUT_PLUGINS = ['output_log', 'output_json']
log_q = Queue.Queue()

class OutputLogger():
    def __init__(self, log_q):
        self.log_q = log_q
        self.debug('OutputLogger init!')

    def debug(self, message):
        level = logging.DEBUG
        self.log_q.put((message, level))

    def info(self, message):
        level = logging.INFO
        self.log_q.put((message, level))

    def error(self, message):
        level = logging.ERROR
        self.log_q.put((message, level))

    def warning(self, message):
        level = logging.WARNING
        self.log_q.put((message, level))

    def write(self, message):
        self.log_q.put(message)

logger = OutputLogger(log_q)

class OutputWriter(threading.Thread):
    def __init__(self):
        logger.debug("Creating OutputWriter!")
        threading.Thread.__init__(self)
        self.process = True
        self.output_writers = []

        for output in OUTPUT_PLUGINS:
            output_writer = __import__('logger.outputs.{}'.format(output),
                                       globals(),
                                       locals(),
                                       ['output']).Output()
            self.output_writers.append(output_writer)

    def run(self):
        logger.debug("Starting OutputWriter!")
        while not log_q.empty() or self.process:
            try:
                log = log_q.get(timeout=.1)
            except Queue.Empty:
                continue
            if isinstance(log, tuple):
                self.log(*log)

            else:
                self.write(log)

            log_q.task_done()

    def stop(self):
        self.process = False

    def write(self, log):
        for writer in self.output_writers:
            writer.write(log)

    def log(self, log, level):
        first_logger = self.output_writers[0]
        if first_logger.__name__ == 'output_log':
            first_logger.write(log, level)

