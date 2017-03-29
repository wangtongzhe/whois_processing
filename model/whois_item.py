import datetime


class WhoisItem(object):
    wid = ""
    domain = ""
    suffix = ""
    trans_obj = None
    trans_sha256 = ""
    add_time = datetime.datetime.now()
    source = None

    def __init__(self, domain, suffix):
        self.domain = domain
        self.suffix = suffix
