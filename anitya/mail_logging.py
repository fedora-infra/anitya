# -*- coding: utf-8 -*-
#
# Copyright © 2014  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#

'''
Mail handler for logging.
'''
import logging
import logging.handlers

import inspect
import os
import socket
import traceback

psutil = None
try:
    import psutil
except (OSError, ImportError):
    # We run into issues when trying to import psutil from inside mod_wsgi on
    # rhel7.  If we hit that here, then just fail quietly.
    # https://github.com/jmflinuxtx/kerneltest-harness/pull/17#issuecomment-48007837
    pass


class ContextInjector(logging.Filter):
    """ Logging filter that adds context to log records.

    Filters are typically used to "filter" log records.  They declare a filter
    method that can return True or False.  Only records with 'True' will
    actually be logged.

    Here, we somewhat abuse the concept of a filter.  We always return true,
    but we use the opportunity to hang important contextual information on the
    log record to later be used by the logging Formatter.  We don't normally
    want to see all this stuff in normal log records, but we *do* want to see
    it when we are emailed error messages.  Seeing an error, but not knowing
    which host it comes from, is not that useful.

    http://docs.python.org/2/howto/logging-cookbook.html#filters-contextual

    This code has been originally written by Ralph Bean for the fedmsg
    project:
        https://github.com/fedora-infra/fedmsg/
    and can be found at:
        https://infrastructure.fedoraproject.org/cgit/ansible.git/tree/roles/fedmsg/base/templates/logging.py.j2

    """

    def filter(self, record):
        current_process = ContextInjector.get_current_process()
        current_hostname = socket.gethostname()

        record.host = current_hostname
        record.proc = current_process
        record.pid = '-'
        if not isinstance(current_process, str):
            record.pid = current_process.pid
        record.proc_name = current_process.name
        record.command_line = " ".join(current_process.cmdline)
        record.callstack = self.format_callstack()
        return True

    @staticmethod
    def format_callstack():
        for i, frame in enumerate(f[0] for f in inspect.stack()):
            if '__name__' not in frame.f_globals:
                continue
            modname = frame.f_globals['__name__'].split('.')[0]
            if modname != "logging":
                break

        def _format_frame(frame):
            return '  File "%s", line %i in %s\n    %s' % (frame)

        stack = traceback.extract_stack()
        stack = stack[:-i]
        return "\n".join([_format_frame(frame) for frame in stack])

    @staticmethod
    def get_current_process():
        mypid = os.getpid()

        if not psutil:
            return "Could not import psutil for %r" % mypid

        for proc in psutil.process_iter():
            if proc.pid == mypid:
                return proc

        # This should be impossible.
        raise ValueError("Could not find process %r" % mypid)


MSG_FORMAT = """Process Details
---------------
host:     %(host)s
PID:      %(pid)s
name:     %(proc_name)s
command:  %(command_line)s

Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:
--------

%(message)s


Callstack that lead to the logging statement
--------------------------------------------
%(callstack)s
"""


def get_mail_handler(smtp_server, mail_admin):
    """ Set up the handler sending emails for big exception
    """
    mail_handler = logging.handlers.SMTPHandler(
        smtp_server,
        'nobody@fedoraproject.org',
        mail_admin,
        'Anitya (server) error')
    mail_handler.setFormatter(logging.Formatter(MSG_FORMAT))
    mail_handler.setLevel(logging.ERROR)
    mail_handler.addFilter(ContextInjector())
    return mail_handler
