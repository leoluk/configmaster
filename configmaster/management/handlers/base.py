#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from contextlib import contextmanager
from configmaster.models import Report


class TaskExecutionError(RuntimeError):
    def __init__(self, message, long_message=None):
        """
        This exception is a shortcut to signal a task failure and is
        equivalent to returning
        :attr:`configmaster.models.Report.RESULT_FAILURE`.

        Args:
            message: Short error message that appears in places like the
                dashboard or the main Nagios check output. Must fit on a single
                line and should not exceed ~30 characters.

            long_message: Verbose error message. Visible in the full report
                view or the full Nagios check output (on the check detail
                page). Put tracebacks or debugging output here.

        """
        super(TaskExecutionError, self).__init__(message)
        self.long_message = long_message


class BaseHandler(object):
    def __init__(self, device):
        """
        Base class for all task execution handlers.

        Args:
            device (configmaster.models.Device): Device to run against. Will
                be available as :attr:`self.device`.
        """
        self.device = device

    @staticmethod
    def _fail(message, *fmt):
        """
        Any fatal error which has been caught should result in a call
        to this method. It raises a TaskExecutionError which is caught by
        the task handler and equivalent to returning
        :attr:`configmaster.models.Report.RESULT_FAILURE`.

        If additional positional arguments are present, the message is
        treated as a format string and formatted with the additional
        arguments.

        Example::

            self._fail("We failed while running %s", subsystem)

        """
        raise TaskExecutionError(message % fmt if fmt else message)

    @staticmethod
    def _fail_long_message(message, long_message, *fmt):
        """
        Fails with a long message.

        See :meth:`_fail` and :exc:`TaskExecutionError` for details.
        """
        raise TaskExecutionError(
            message % fmt if fmt else message, long_message
        )

    @staticmethod
    def _return_success(message, *args):
        """
        Shortcut, returns :attr:`configmaster.models.Report.RESULT_SUCCESS`
        with the specified message.

        If additional positional arguments are present, the message is
        treated as a format string and formatted with the additional
        arguments (see :meth:`_fail`).

        Example::

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
        This method should execute the task and return a ``(exit_code,
        output)`` tuple. This method should only be implemented by task
        handlers which are called from the task runner.

        See :mod:`task runner docs <configmaster.management.commands.run>`.
        """
        return self._return_success("We successfully did nothing at all")

    def cleanup(self):
        """
        This method is called if an exception occurs during the task run.

        Does nothing by default.
        """
        pass

    @classmethod
    def run_completed(cls):
        """
        Called by the task runner once for every task type after a run is
        complete. This method should be used for actions which should only
        be executed once per task (example: git push).

        Does nothing by default.
        """
        pass