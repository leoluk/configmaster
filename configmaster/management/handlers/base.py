from contextlib import contextmanager
from configmaster.models import Report


class TaskExecutionError(RuntimeError):
    def __init__(self, message, long_message=None):
        super(TaskExecutionError, self).__init__(message)
        self.long_message = long_message


class BaseHandler(object):
    def __init__(self, device):
        """
        Base class for all task execution handlers.
        :type device: configmaster.models.Device
        """
        self.device = device

    @staticmethod
    def _fail(message, *fmt):
        """
        Any fatal error which has been caught should result in a call
        to this method. It raises a TaskExecutionError which is caught by
        the task handler and equivalent to returning Report.RESULT_FAILURE.

        If additional positional arguments are present, the message is
        treated as a format string and formatted with the additional
        arguments.

        Example:

            self._fail("Something bad happened with subsystem %s", subsystem)

        """
        raise TaskExecutionError(message % fmt if fmt else message)

    @staticmethod
    def _fail_long_message(message, long_message, *fmt):
        """
        See _fail.

        long_message is stored in an additional field in the database, but
        not shown in the dashboard.
        """
        raise TaskExecutionError(
            message % fmt if fmt else message, long_message
        )

    @staticmethod
    def _return_success(message, *args):
        """
        Shortcut, returns Report.RESULT_SUCCESS with the specified message.

        If additional positional arguments are present, the message is
        treated as a format string and formatted with the additional
        arguments (see _fail).

        Example:

            return self._return_success("Everything worked!")

        """
        return Report.RESULT_SUCCESS, (message % args if args else message)

    @contextmanager
    def run_wrapper(self, *args, **kwargs):
        """
        This method is called as a context manager for the run method. Any
        behaviour which should be inherited to descendant classes must be
        defined here (SSH connection handling, for example).

        If this method is overwritten by a child, the inherited method must
        be called as a context manager. This allows the parent class to
        define behaviour before and after the invocation of the descendant's
        method (catching exceptions, for example).
        """
        yield

    def run(self, *args, **kwargs):
        """
        This method should execute the task and return a (exit_code,
        output) tuple. This method should only be implemented by task handlers
        which are called from the task runner.

        See task runner documentation.
        """
        return self._return_success("We successfully did nothing at all")

    def cleanup(self):
        """
        This method is called if an exception occurs during the task run.
        """
        pass

    @classmethod
    def run_completed(cls):
        """
        Called by the task runner once for every task type after a run is
        complete. This method should be used for actions which should only
        be executed once per task (example: git push).
        """
        pass