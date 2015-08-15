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

import os
import sys
import glob
import shutil

from contextlib import suppress

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


#
# File system
# ^^^^^^^^^^^

class fs(object):
    """Namespace for filesystem related operations."""

    @staticmethod
    def shexpand(pattern):
        """Return a possibly-empty list of path names that match
        *pattern*.

        :param pattern: A string or a list of strings containing
                        shell-style wildcards.
        :type pattern: str or iterable

        :returns: A list of path names matching given *pattern*.
        :rtype: list

        """
        if isinstance(pattern, (str, bytes)):
            it = [pattern, ]
        else:
            it = pattern

        def _expand(x):
            return glob.glob(os.path.expanduser(os.path.expandvars(x)))

        # Flatten list of paths from _expand.
        return [
            item
            for paths_list in map(_expand, it)
            for item in paths_list
        ]


    @staticmethod
    def copytree(src, dst):
        """Copy the directory tree structure from *src* to recreate it
        in the *dst* directory.

        :param str src: Path to the source to replicate the directory
                        tree structure from.

        :param str dst: Path to the destination directory to replicate
                        the directory tree structure.

        """
        os.makedirs(dst, exist_ok=True)
        for root, dirs, _ in os.walk(src):
            for d in dirs:
                os.makedirs(
                    os.path.join(root.replace(src, dst), d),
                    exist_ok=True
                )


    @classmethod
    def lstree(cls, pattern, recursive=False, include_path=False):
        """List all files and directories found in given path.

        :param iterable pattern: A string or list of strings containing
                                 shell-style patterns of directories to
                                 remove.

        :param bool recursive: Should the content of any directory
                               found in ``path`` also be listed?
                               Default to **False**.

        :param bool include_path: Should given ``path`` also be included
                                  in returned list.

        :returns: A list of items found in given path.
        :rtype: list

        """
        lst = []
        for path in cls.shexpand(pattern):
            for root, dirs, files in os.walk(path):
                if root == path and include_path:
                    lst.append(root)

                lst += map(lambda x: os.path.join(root, x), dirs)
                lst += map(lambda x: os.path.join(root, x), files)

                if not recursive:
                    break

        return lst


    @classmethod
    def rmdir(cls, pattern, recursive=False):
        """Remove empty directory at *path*. When recursive is set to
        ``True``, run over the directory tree to remove any empty
        directory found.

        :param iterable pattern: A string or list of strings containing
                                 shell-style patterns of directories to
                                 remove.

        :param bool recursive: Should *path* be walked through to remove
                               empty directories found in the tree?

        """
        for path in sorted(cls.shexpand(pattern)):
            if recursive:
                # Remove empty directories in tree from deepest to
                # shallowest.
                for root, dirs, _ in os.walk(path, topdown=False):
                    for d in dirs:
                        with suppress(OSError):
                            os.rmdir(os.path.join(root, d))

            with suppress(OSError):
                os.rmdir(path)


    @classmethod
    def rmtree(cls, pattern):
        """Remove directory trees matching given Unix shell style
        patterns.

        :param iterable pattern: A string or list of strings containing
                                 shell-style patterns of directories to
                                 remove.

        """
        for path in sorted(cls.shexpand(pattern)):
            # Avoid two removal tries if path does not exist.
            if not os.path.lexists(path):
                continue

            try:
                # Try to remove path (and sub-paths) as a directory.
                shutil.rmtree(path)
            except OSError:
                # Not a directory, try to remove path as a file.
                with suppress(OSError):
                    os.remove(path)


    @classmethod
    def symlink(cls, source, link_name, force=False, target_is_directory=False):
        """Create a symbolic link pointing to *source* named *link_name*.

        :param str source: Path of the target to link to.
        :param str link_name: Path to the symbolic link to create.
        :param bool force: If set to ``True`` if *link_name* exists, it
                           will be removed before creating the link.
                           Default to ``False``.
        :param bool target_is_directory:
          On Windows, a symlink represents either a file or a directory
          and does not morph to the target dynamically. Symlink will be
          created as a directory if set to ``True``. Default to
          ``False``.

        :returns: ``True`` if symlink creation suceeded, ``False``
                  otherwise.
        :rtype: bool

        """
        with suppress(OSError):
            if os.readlink(link_name) == source \
               or os.path.abspath(os.readlink(link_name)) == source:
                return True

        if force:
            if os.path.lexists(link_name):
                cls.rmtree(link_name)
            else:
                try:
                    os.makedirs(link_name, exist_ok=True)
                except OSError:
                    return False
                cls.rmdir(link_name)

        try:
            os.symlink(
                source, link_name, target_is_directory=target_is_directory
            )
        except (NotImplementedError, OSError):
            return False

        return True

