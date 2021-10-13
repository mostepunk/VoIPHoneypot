import os


TEMPLATES_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ),
           'webserver/templates/')

print(TEMPLATES_DIR)
