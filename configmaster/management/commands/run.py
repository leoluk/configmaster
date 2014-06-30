from django.core.management import BaseCommand
import re
import traceback
from configmaster.management import handlers
from configmaster.management.handlers.base import TaskExecutionError
from configmaster.models import Device, Report

RE_MATCH_SINGLE_WORD = re.compile(r'\A[\w-]+\Z')


class Command(BaseCommand):
    """
    This management command contains the runner, which iterates over all
    devices in the database and executed any tasks which have been defined
    for them. It is designed to be called from a

    The runner instantiates a handler class for each task, which is defined
    in the database and imported from the management.handlers module. Each
    class should define two interfaces: run_complete(), run_wrapper() and
    run(). The wrapper is called as a context manager and wraps the run()
    invocation and performs setup- and clean-up-tasks (opening connections,
    removing temporary files...). run() is called with no arguments,
    and should execute the task itself. It should return a (exit_status,
    output) tuple. The exit status should be either Report.RESULT_SUCCESS or
    Report.RESULT_FAILURE. The run_complete method is called *once per task*
    at the end of each run.

    Instead of retuning Report.RESULT_FAILURE, a task handler may raise a
    TaskExecutionError exception.

    The command line output of this command is just for debugging purposes
    (except for the run_completed handler), as all task output is logged to
    the database (as reports).

    Exceptions raised during normal operation should be caught within the
    task handler (connection timeouts...). Unexpected runtime errors will be
    caught by the task runner and logged with full details (i.e. traceback).

    """

    # TODO: Refactor the task runner (too many levels of indentation)
    # The task runner logic should be decoupled from the management
    # command. This is required for T47 (manual runs).

    help = "Config management run"

    # noinspection PyBroadException
    def handle(self, *args, **options):
        call_after_completion = dict()

        for device in Device.objects.all():
            if device.device_type is None:
                self.stdout.write("Device %s has no device type, skipping..." % device.label)
                continue
            elif (not device.enabled) or (not device.group.enabled):
                self.stdout.write("Device %s is disabled, skipping..." % device.label)
                continue
            else:
                if not device.device_type.tasks.count():
                    self.stdout.write("No tasks for %s" % device.label)
                    continue

                self.stdout.write("Processing %s..." % device.label)

                for task in device.device_type.tasks.all():
                    if not task.enabled:
                        self.stdout.write('Device %s, task "%s" skipped (disabled)'
                                          % (device.label, task.name))
                        continue
                    report = Report()
                    try:
                        # Make sure that the class name read from the database
                        # is one single word as a precaution and get it from
                        # the management.handlers module, which is already
                        # imported.

                        if RE_MATCH_SINGLE_WORD.match(task.class_name):
                            try:
                                handler_obj = getattr(handlers, task.class_name)(device)
                            except AttributeError:
                                raise TaskExecutionError('Handler class "%s" not found'
                                                         % task.class_name)

                            # Invoke the task handler methods (main part!)

                            with handler_obj.run_wrapper():
                                _result = handler_obj.run()
                            if _result is None:
                                raise TaskExecutionError("Task handler did not return any data")

                            # Add the run_completed handler to a dictionary
                            # in order to call it after the run is completed.
                            # This ensures that each handler is only called once.

                            call_after_completion[task.name] = handler_obj.run_completed

                            result, output = _result

                        elif not task.class_name:
                            raise TaskExecutionError("Empty handler class name")
                        else:
                            raise TaskExecutionError("Invalid handler class name: %s"
                                                     % device.device_type.handler)

                    # Convert TaskExecutionError exceptions to regular task
                    # output (see command documentation). Instead of raising
                    # this exception, a task could set the Report.RESULT_FAILURE
                    # result manually.

                    except TaskExecutionError, e:
                        result = Report.RESULT_FAILURE
                        output = str(e)

                    # Catch any exception raised by the task and log it to
                    # the database. The Report.long_output field is not shown
                    # in the status table in the frontend, so it's okay to put
                    # long text in it (in this case a full traceback).

                    except Exception, e:
                        result = Report.RESULT_FAILURE
                        output = (u"Uncaught {}, message: {}"
                                  .format(type(e).__name__, str(e)))
                        report.long_output = traceback.format_exc()


                    if result == Report.RESULT_FAILURE:
                        self.stderr.write('Device %s, task "%s" failed: %s'
                                          % (device.label, task.name, output))
                        if report.long_output:
                            self.stderr.write(report.long_output)
                    else:
                        self.stdout.write('Device %s, task "%s" succeeded'
                                          % (device.label, task.name))
                        self.stdout.write("Output: %r" % output)

                    report.device = device
                    report.result = result
                    report.task = task
                    report.output = output
                    report.save()


        # Call run_complete methods of all invoked task handlers

        for task_name, func in call_after_completion.iteritems():
            self.stdout.write('Calling run_complete for task "%s"...' % task_name)
            func()

        self.stdout.write("Run completed.")
