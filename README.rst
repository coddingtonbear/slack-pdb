slackpdb - Remotely and collaboratively debug your Python application via a Slack channel
=========================================================================================

.. image:: https://travis-ci.org/coddingtonbear/slackpdb.svg?branch=master
    :target: https://travis-ci.org/coddingtonbear/slackpdb

Slackpdb is an adaptation of rpdb that, instead of opening a port and
allowing you to debug over telnet, connects to a configurable Slack
channel so you can collaboratively debug an application remotely.

.. code-block::

    import slackpdb
    slackpdb.set_trace(
        token="<your slack token>",
        channel="#debugger_hangout",
    )

Upon reaching ``set_trace()``, your script will "hang" and the only way to get
it to continue is to access slackpdb by talking to the user that connected to the
above IRC channel.

To interact with the debugger, just send messages in the channel prefixed
with the username it announces itself as, or simply "!".

For example, the following two commands are equivalent, and each will
display the pdb help screen (be sure to replace 'MyHostname' with whatever
username the bot selected)::

    !help

::

    slackpdb: help

Installation
------------

From ``pip``::

    pip install slackpdb

Options
-------

* ``token``: A token to use for connecting to Slack; if you do not have one,
  you can quickly generate one at https://my.slack.com/services/new/bot.  Note
  that if this is not specified, it may be gathered from the SLACK_API_TOKEN
  environment variable, or, if the ``django`` option is set to ``True``, from
  a Django setting named ``SLACK_API_TOKEN``.
* ``channel`` (**REQUIRED**): The name of the channel (starting with ``#``).
* ``limit_access_to``: A list of nicknames that
  are allowed to interact with the debugger.
* ``activation_timeout``: Wait maximally this number of seconds for
  somebody to interact with the debugger in the channel before
  disconnecting and continuing execution.  Default: ``60`` seconds.
* ``django``: (Default: ``False``) Attempt to gather Slack API token from
  a django setting named ``SLACK_API_TOKEN`` if otherwise unspecified.

Security Disclaimer
-------------------

The way that this library works is **inherently** **dangerous**; given that
you're able to execute arbitrary Python code from within your debugger,
it is strongly recommended that you take all reasonable measures to ensure
that you control who are able to execute debugger commands.

Just to make absolutely sure this is clear: you're both responsible for
determining what level of risk you are comfortable with, and for taking
appropriate actions to mitigate that risk.

As is clearly and thunderously stated library's license (see the included
``LICENSE.txt``)::

    THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
    OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
    HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
    LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
    OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
    SUCH DAMAGE.

Good luck, and happy debugging!

Troubleshooting
---------------

If you do not see the bot entering your specified channel, try increasing
the logging level by adding the following lines above your trace to gather
a little more information about problems that may have occurred while 
connecting to the IRC server:

.. code-block::

   import logging
   logging.basicConfig(filename='/path/to/somewhere.log', level=logging.DEBUG)

Author(s)
---------
Adam Coddington <me@adamcoddington.net> - http://adamcoddington.net/

This library is a fork of rpdb, and the underpinnings of this library
are owed to Bertrand Janin <b@janin.com> - http://tamentis.com/ and
all other contributors to `rpdb <https://github.com/tamentis/rpdb>`
including the following:

 - Ken Manheimer - @kenmanheimer
 - Steven Willis - @onlynone
 - Jorge Niedbalski R <niedbalski@gmail.com>
 - Cyprien Le Pannérer <clepannerer@edd.fr>
 - k4ml <kamal.mustafa@gmail.com>
 - Sean M. Collins <sean@coreitpro.com>
