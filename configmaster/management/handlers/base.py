from configmaster.models import Report


class BaseHandler(object):
    def __init__(self, device):
        self.device = device

    def run(self, *args, **kwargs):
        return Report.RESULT_SUCCESS, "We successfully did nothing at all"