import logging
import os
import pdb
import socket
import sys
from threading import Thread
import traceback

import six

from .bot import SlackpdbBot


logger = logging.getLogger(__name__)


DEFAULT_PARAMS = {
    'channel': '#debugger',
}


class Slackpdb(pdb.Pdb):
    def __init__(self, token, **kwargs):
        """Initialize the socket and initialize pdb."""
        params = DEFAULT_PARAMS.copy()
        params.update(kwargs)

        # Backup stdin and stdout before replacing them by the socket handle
        self.old_stdout = sys.stdout
        self.old_stdin = sys.stdin
        self.read_timeout = 0.1

        if not token:
            raise ValueError("A slack API token must be provided.")
        if not params.get('limit_access_to'):
            logger.warning(
                "No nickname limitations set!  Any user talking to the "
                "debugger user can execute arbitrary code on the host "
                "machine!"
            )
        elif isinstance(params.get('limit_access_to'), six.string_types):
            params['limit_access_to'] = [params.get('limit_access_to')]

        connect_params = {}
        if not params.get('channel'):
            raise ValueError(
                "You must specify a channel to connect to using the "
                "`channel` keyword argument."
            )

        # Writes to stdout are forbidden in mod_wsgi environments
        try:
            logger.info(
                "slackpdb has connected to slack in %s\n",
                params.get('channel')
            )
        except IOError:
            pass

        r_pipe, w_pipe = os.pipe()
        # The A pipe is from the bot to pdb
        self.p_A_pipe = os.fdopen(r_pipe, 'r')
        self.b_A_pipe = os.fdopen(w_pipe, 'w')

        r_pipe, w_pipe = os.pipe()
        # The B pipe is from pdb to the bot
        self.b_B_pipe = os.fdopen(r_pipe, 'r')
        self.p_B_pipe = os.fdopen(w_pipe, 'w')

        pdb.Pdb.__init__(
            self,
            stdin=self.p_A_pipe,
            stdout=self.p_B_pipe,
        )

        self.bot = SlackpdbBot(
            token=token,
            channel=params.get('channel'),
            limit_access_to=params.get('limit_access_to'),
            activation_timeout=params.get('activation_timeout', 60),
            **connect_params
        )

    def shutdown(self):
        """Revert stdin and stdout, close the socket."""
        sys.stdout = self.old_stdout
        sys.stdin = self.old_stdin
        pipes = [
            self.p_A_pipe,
            self.p_B_pipe,
            self.b_A_pipe,
            self.b_B_pipe
        ]
        for pipe in pipes:
            try:
                pipe.close()
            except IOError:
                logger.warning(
                    "IOError encountered while closing a pipe; messages "
                    "may have been lost."
                )

    def do_continue(self, arg):
        """Clean-up and do underlying continue."""
        try:
            return pdb.Pdb.do_continue(self, arg)
        finally:
            self.shutdown()

    do_c = do_cont = do_continue

    def do_quit(self, arg):
        """Clean-up and do underlying quit."""
        try:
            return pdb.Pdb.do_quit(self, arg)
        finally:
            self.shutdown()

    do_q = do_exit = do_quit


def set_trace(*args, **kwargs):
    """Wrapper function to keep the same import x; x.set_trace() interface.

    We catch all the possible exceptions from pdb and cleanup.

    """
    debugger = Slackpdb(*args, **kwargs)
    if not args and os.environ.get('SLACK_API_TOKEN'):
        args = (os.environ.get('SLACK_API_TOKEN'), )
    if not args and kwargs.get('django', False):
        from django.conf import settings
        args = (settings.SLACK_API_TOKEN, )
        kwargs.pop('django')

    try:
        slack_feeder = Thread(
            target=debugger.bot.process_forever,
            args=(debugger.b_B_pipe, debugger.b_A_pipe, ),
        )
        slack_feeder.daemon = True
        slack_feeder.start()

        debugger.set_trace(sys._getframe().f_back)
    except Exception:
        debugger.shutdown()
        traceback.print_exc()
