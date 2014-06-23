from configmaster.models import Report


class TaskExecutionError(RuntimeError): pass


class BaseHandler(object):
    def __init__(self, device):
        """
        :type device: configmaster.models.Device
        """
        self.device = device

    @staticmethod
    def _fail(message, *args):
        raise TaskExecutionError(message % args if args else message)

    @staticmethod
    def _return_success(message, *args):
        return Report.RESULT_SUCCESS, (message % args if args else message)

    def run(self, *args, **kwargs):
        return self._return_success("We successfully did nothing at all")