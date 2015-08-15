#
# tasks.py
# ========
#
# Copying
# -------
#
# Copyright (c) 2015 propanelib authors and contributors.
#
# This file is part of the *propanelib* project.
#
# propanelib is a free software project. You can redistribute it and/or
# modify if under the terms of the MIT License.
#
# This software project is distributed *as is*, WITHOUT WARRANTY OF ANY
# KIND; including but not limited to the WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE and NONINFRINGEMENT.
#
# You should have received a copy of the MIT License along with
# propanelib. If not, see <http://opensource.org/licenses/MIT>.
#
"""Management tasks definition to ease propanelib development."""

import re

import sys

from invoke import Collection


#
# Global definitions
# ------------------

ns = Collection()


#
# Utility functions
# -----------------

#
# Input / Output
# ^^^^^^^^^^^^^^

class msg(object):
    """Namespace for message printing operations.

    :attribute REQUEST: Message is requesting an input from the user.

    :attribute INFORMATION: Message is informative with no potential
                            impact.

    :attribute WARNING: Message to attract user attention or to warn
                        about an unexpected behaviour but with little
                        impact.

    :attribute ERROR: A error occured during task execution but did not
                      discontinue execution.

    :attribute FATAL: A non-recoverable error occured and discontinued
                      task execution.

    """
    _NOPREFIX   = 1 << 0
    _CONTINUE   = 1 << 1
    REQUEST     = 1 << 2
    INFORMATION = 1 << 3
    WARNING     = 1 << 4
    ERROR       = 1 << 5
    FATAL       = 1 << 6

    _levels = {
        _NOPREFIX:   ('',   sys.stdout),
        _CONTINUE:   ('..', sys.stdout),
        REQUEST:     ('>>', sys.stdout),
        INFORMATION: ('ii', sys.stdout),
        WARNING:     ('!!', sys.stdout),
        ERROR:       ('EE', sys.stderr),
        FATAL:       ('XX', sys.stderr),
    }


    @classmethod
    def write(cls, level, *lines):
        """Print *lines* to the standard output at given *level*.

        :param int level: Level of the message to be printed. Allowed
                          values are:

                          - :attr:`msg.REQUEST`
                          - :attr:`msg.INFORMATION`
                          - :attr:`msg.WARNING`
                          - :attr:`msg.ERROR`
                          - :attr:`msg.FATAL`

        :param str lines: Lines to be printed on screen.

        """
        prefix, stream = cls._levels.get(
            level, cls._levels[cls._NOPREFIX]
        )
        c_prefix, c_stream = prefix, stream
        # Message upper than INFORMATION level should be visible to
        # the user so the prefix for those messages is kept.
        if level < cls.WARNING:
            c_prefix, c_stream = cls._levels[cls._CONTINUE]

        lines = list(lines)
        print(prefix, lines.pop(0), sep=' ', file=stream)
        for l in lines:
            print(c_prefix, l, sep=' ', file=c_stream)


    @classmethod
    def ask(cls, *lines, **kwargs):
        """Request input from the user and return the result. *lines*
        are printed using the :attr:`msg.REQUEST` level. The last
        line should be the request to the user printed as such::

            >> Enter your full name:_

        In the previous example, *Enter your full name:* is the last
        line provided and the character ``_`` represents a white space
        which is added by this function.

        If *request_only* is given, this should be only as a keyword
        argument.

        :param str lines: Lines to be printed on screen. If multiple
                          lines are given, the first lines are
                          information to the user while the last line is
                          the actual question.

        :param bool request_only: Should only the request be printed and
                                  skip the message? Default to ``False``.

        :returns: Input provided by the user.
        :rtype: str

        """
        lines   = list(lines)
        request = '{prefix} {message} '.format(
            prefix=cls._levels[cls.REQUEST][0], message=lines.pop()
        )

        if lines and not kwargs.get('request_only', False):
            cls.write(cls.REQUEST, *lines)
        return input(request)


    @classmethod
    def ask_yn(cls, *lines, **kwargs):
        """Ask a question on which the user has to reply *yes* or *no*.
        *lines* are printed using the :attr:`msg.REQUEST` level. The last
        line should be the question asked to the user and is printed as
        such::

            >> Question? [y/n]_

        In above example, ``Question?`` is the last line provided and
        the character ``_`` represents a white space which is added by
        this function..

        :param str lines: Lines to be printed on screen. If multiple
                          lines are given, the first lines are
                          information to the user while the last line is
                          the actual question.

        :param bool default: When ``True``, *yes* will be the default
                             value if the user provides no entry. When
                             ``False``, the default value is *no*. If
                             not given, question will be asked to the
                             user a maximum of 3 times before returning.

        :returns: ``True`` if user's reply is *yes*, ``False`` if user's
                  reply is *no*. Returns ``None`` when no valid answer
                  could be gotten from the user.

        :rtype: bool or None

        """
        valid_yes_re = re.compile(r'y|yes|t|true|1', re.IGNORECASE)
        valid_no_re  = re.compile(r'n|no|f|false|0', re.IGNORECASE)
        max_try = 2

        # Prepare available options based on expected default answer.
        default = kwargs.get('default')
        opts = '[y/n]'
        if default is True:
            opts = '[Y/n]'
        elif default is False:
            opts = '[y/N]'

        # Add options to the request.
        lines = list(lines)
        lines.append(
            '{message} {opts}'.format(message=lines.pop(), opts=opts)
        )

        answer = cls.ask(*lines)
        while max_try != 0:
            if valid_yes_re.match(answer):
                return True
            elif valid_no_re.match(answer):
                return False
            elif default is not None:
                return default

            answer   = cls.ask(*lines, request_only=True)
            max_try -= 1

        return None

