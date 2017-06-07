import fcntl
import logging
from multiprocessing import Queue
import os
import random
import socket
import textwrap
import time

import six
from slackclient import SlackClient

from .exceptions import SlackpdbError


logger = logging.getLogger(__name__)


class SlackpdbBot(SlackClient):
    PROMPT = u'_Ready for command..._'

    _CHANNEL_INFO = {}
    _USER_INFO = {}

    def __init__(
        self, token, channel, limit_access_to, activation_timeout,
        **connect_params
    ):
        self.token = token
        self.channel = channel
        self.queue = Queue()
        self.activated = False
        self.activation_timeout = activation_timeout
        self.limit_access_to = limit_access_to

        super(SlackpdbBot, self).__init__(token)

        self.token_info = self.get_token_info()
        self.channel_info = self.get_debugger_channel_info()

    def send_welcome(self):
        self.send_channel_message(
            [
                u"*Debugger ready on host %s*" % socket.gethostname(),
                (
                    (
                        u"_The following users are able to interact with this "
                        u"debugger: %s._" % (
                            ', '.join(self.limit_access_to)
                        )
                    ) if self.limit_access_to else (
                        u"_All users in this channel can interact with this "
                        u"debugger._"
                    )
                ),
                (
                    u"_Please prefix debugger commands with either '!' or "
                    u"'%s:'. For pdb help, say '!help'; for a list of "
                    u"slackpdb-specific commands, say '!!help'._" % (
                        self.token_info['user'],
                    )
                )
            ],
            as_snippet=False,
        )

    def get_token_info(self):
        result = self.api_call('auth.test')

        if not result.get('ok'):
            raise ValueError('Unable to find username!')

        return result

    def get_debugger_channel_info(self):
        channels = self.api_call('channels.list')['channels']

        for channel in channels:
            if channel.get('name') == self.channel.strip('#'):
                return self.get_channel_info(channel.get('id'))

        raise ValueError('Specified channel does not exist!')

    def get_user_info(self, user):
        if not user:
            return {}
        if user not in self._USER_INFO:
            result = self.api_call(
                'users.info',
                user=user
            )

            if result.get('ok'):
                self._USER_INFO[user] = result['user']

        return self._USER_INFO.get(user, {})

    def get_channel_info(self, channel):
        if not channel:
            return {}
        if channel not in self._CHANNEL_INFO:
            result = self.api_call(
                'channels.info',
                channel=channel
            )

            if result.get('ok'):
                self._CHANNEL_INFO[channel] = result['channel']

        return self._CHANNEL_INFO.get(channel, {})

    def message_should_be_processed(self, message):
        if message.get('type') != 'message':
            return False

        if message.get('edited'):
            logger.warning(
                "Ignoring edited message: %s",
                message,
            )
            return False

        channel = self.get_channel_info(message.get('channel'))

        if channel.get('name') != self.channel.strip('#'):
            return False

        user = self.get_user_info(message.get('user'))
        if not channel or not user:
            return False

        if message.get('user') == self.token_info['user_id']:
            return False

        if not channel.get('is_channel', False):
            return False

        try:
            prefix, message = (
                message.get('text', '').split(' ', 1)
            )
        except ValueError:
            return False

        if (
            prefix.strip(':').strip('@').strip('<').strip('>')
            in (
                self.token_info['user'],
                self.token_info['user_id'],
            )
        ):
            return False

        if (
            self.limit_access_to
            and user.get('name') not in self.limit_access_to
        ):
            return False

        return True

    def send_user_message(self, nickname, message):
        if not isinstance(message, six.text_type):
            message = u'\n'.join(message)

        logger.debug(
            "Sending user '%s' message '%s'.",
            nickname,
            message,
        )

        result = self.api_call(
            'chat.postMessage',
            channel=nickname,
            text=message,
            username=self.token_info['user'],
            as_user=False,
        )

        logger.debug(
            "Result: %s",
            result,
        )

    def send_channel_message(self, message, as_snippet=True):
        if not isinstance(message, six.text_type):
            message = u'\n'.join(message)

        logger.debug(
            "Sending channel '%s' %s.",
            message,
            'as snippet' if as_snippet else 'as message'
        )

        if as_snippet:
            result = self.api_call(
                'files.upload',
                channels=self.channel,
                filetype='python',
                content=message,
            )
        else:
            result = self.api_call(
                'chat.postMessage',
                channel=self.channel,
                text=message,
                username=self.token_info['user'],
                as_user=False,
            )

        logger.debug(
            "Result: %s",
            result,
        )

    def do_command(self, message, ):
        self.activated = True

        _, cmd = message.get('text').split(' ', 1)
        user = self.get_user_info(message.get('user'))

        logger.debug('Received command: %s', message)

        nickname = user.get('name')

        if cmd.startswith("!allow"):
            allows = cmd.split(' ')
            usernames = allows[1:]
            if not self.limit_access_to:
                self.limit_access_to.append(nickname)
            self.limit_access_to.extend(usernames)
            self.send_channel_message(
                u"The following users have been granted access to the "
                u"debugger: %s." % (
                    ', '.join(usernames)
                )
            )
        elif cmd.startswith("!forbid"):
            forbids = cmd.split(' ')
            usernames = forbids[1:]
            try:
                for username in usernames:
                    self.limit_access_to.remove(username)
                self.send_channel_message(
                    u"The following users have been forbidden access to the "
                    u"debugger: %s." % (
                        ', '.join(usernames)
                    )
                )
            except ValueError:
                self.send_channel_message(
                    u"The users %s are not in the 'allows' list.  You must "
                    u"have a defined 'allows' list to remove users from "
                    u"it." % (
                        ', '.join(usernames)
                    )
                )
            if not self.limit_access_to:
                self.send_channel_message(
                    u"All users are allowed to interact with the debugger. "
                )
        elif cmd.startswith("!help"):
            available_commands = textwrap.dedent(u"""
                Available Commands:
                * !!allow NICKNAME
                  Add NICKNAME to the list of users that are allowed to
                  interact with the debugger. Current value: {limit_access_to}.

                * !!forbid NICKNAME
                  Remove NICKNAME from the list of users that are allowed
                  to interact with the debugger.
            """.format(
                limit_access_to=self.limit_access_to,
            ))
            self.send_channel_message(
                available_commands,
            )
        else:
            logger.debug(
                'Sending command `%s` to debugger for message %s',
                cmd.strip(),
                message,
            )
            self.queue.put(cmd.strip())

    def send_prompt(self):
        self.send_channel_message(self.PROMPT, as_snippet=False)

    def api_call(self, *args, **kwargs):
        logger.debug('Sending API command: %s %s', args, kwargs)
        result = super(SlackpdbBot, self).api_call(*args, **kwargs)
        logger.debug('Received API result: %s', result)

        return result

    def process_forever(self, inhandle, outhandle, timeout=0.1):
        # Let's mark out inhandle as non-blocking
        fcntl.fcntl(inhandle, fcntl.F_SETFL, os.O_NONBLOCK)
        # Used for keeping track of when the bot was started
        # so we can disconnect for inactivity.
        started = time.time()
        # Keeps track of whether or not we're in the process of
        # disconnecting (queued the 'q' command)
        disconnecting = False

        if not self.rtm_connect():
            raise SlackpdbError("Unable to connect to Slack RTM service.")

        self.send_welcome()

        if self.token_info['user_id'] not in self.channel_info['members']:
            self.send_channel_message(
                '*The debugger is not currently invited to this channel! '
                'The debugger bot must be in this channel for you to interact '
                'with it; please invite it by saying `/invite @%s`.*' % (
                    self.token_info['user']
                ),
                as_snippet=False,
            )

        while True:
            try:
                messages = inhandle.read()
            except IOError:
                messages = None
            if messages:
                for message in messages.split('(Pdb)'):
                    stripped = message.strip()
                    if stripped:
                        logger.debug('>> %s', stripped)
                        self.send_channel_message(stripped.decode('utf8'))
                self.send_prompt()

            messages = self.rtm_read()
            for message in messages:
                logger.debug('Incoming RTM: %s', message)
                if self.message_should_be_processed(message):
                    self.do_command(message)

            while True:
                if self.queue.empty():
                    break
                message = self.queue.get(block=False)
                logger.debug('<< %s', message)
                outhandle.write(u'%s\n' % message)
                outhandle.flush()

            if (
                time.time() > started + self.activation_timeout and
                not self.activated and
                not disconnecting
            ):
                self.send_channel_message(
                    u"No response received within %s seconds; "
                    u"disconnecting due to inactivity." % (
                        self.activation_timeout
                    ),
                    as_snippet=False,
                )
                disconnecting = True
                self.queue.put('c')
