from configmaster.management.handlers import BaseHandler


class FirewallHandler(BaseHandler):
    def run(self, *args, **kwargs):
        return super(FirewallHandler, self).run(*args, **kwargs)