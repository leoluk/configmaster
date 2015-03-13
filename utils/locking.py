import os
import fcntl

class FileLock(object):
    def __init__(self, name):
        filename = os.path.join(
            "/dev/shm",
            "configmaster-lock-"+name.lstrip('/').replace("/", "-")
        )
        self.f = open(filename, 'w')
        self.acquired = False

    def acquire(self, non_blocking=False):
        fcntl.flock(self.f.fileno(), fcntl.LOCK_EX|(fcntl.LOCK_NB if non_blocking else 0))
        self.acquired = True

    def release(self):
        fcntl.flock(self.f.fileno(), fcntl.LOCK_UN)
        self.acquired = False


class LockMixin(object):
    # Django model mixin

    def __init__(self, *args, **kwargs):
        super(LockMixin, self).__init__(*args, **kwargs)
        self._lock = None

    @property
    def lock(self):
        if not self._lock:
            self._lock = FileLock(
                "/%s/%d" % (type(self).__name__.lower(), self.id)
            )
        return self._lock