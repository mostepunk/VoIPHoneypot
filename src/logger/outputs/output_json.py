import json
import os


#with open('log_config.json', 'r') as json_file:
    #config = json.load(json_file)
#log_dir = config["logs_path"]

log_dir = "/temp/cowrie/data/log"

class Output(object):
    def __init__(self):
        self.__name__ = "output_json"
        self.base = log_dir
        fn = "dlink.json"
        self.fp = os.path.join(self.base, fn)

    def write(self, jsonlog):
        if not os.path.exists(self.base):
            os.makedirs(self.base)
        with open(self.fp, 'a') as f:
            json.dump(jsonlog, f)
            f.write('\n')
            f.flush()
