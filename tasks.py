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

import yaml
import jinja2

from copy import deepcopy
from functools import reduce
from contextlib import suppress

from invoke import Collection, task, run


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


#
# Docstring
# ^^^^^^^^^

class docstring(object):
    """Namespace for docstring operations.

    :attribute COMMENT_START_WITH: Normal comment line identifier.
    :attribute DOCSTRING_START_WITH: Docstring comment line identifier.

    """
    COMMENT_START_WITH = '#'
    DOCSTRING_START_WITH = '#:'

    DOCSTRING_INDENT = 2

    EXT_CF  = '.cf'
    EXT_RST = '.rst'


    @classmethod
    def extract(cls, path, dst, insert_code=False):
        """Extract specially formatted comment strings (a.k.a.
        docstrings) from file and save the result in *dst*.

        Docstring comments should start with ``#:``.

        :param str path: Path of the file from which to extract the
                         docstrings.
        :param str dst: Path to the file in which to write extracted
                        docstrings.

        :param bool insert_code: Shall the documented code also be
                                 inserted in the resulting document?
                                 Defaults to ``False``.

        :returns: ``True`` if result file has been written, ``False``
                  otherwise.
        :rtype: bool

        """
        docstring_start_re = re.compile(
            r'{}\s?'.format(cls.DOCSTRING_START_WITH)
        )

        doclines = []
        doc_app  = doclines.append
        with suppress(OSError), open(path, 'r') as fd:
            code_block = False

            for line in fd:
                # Strip line to get the comment symbol on first position.
                sline = line.strip()

                # Start by looking if we have a docstring.
                if sline.startswith(cls.DOCSTRING_START_WITH):
                    # Insert blank line between previous code block
                    # and next docstring line.
                    if code_block:
                        doc_app('\n')
                        code_block = False

                    ds_line = docstring_start_re.sub('', sline)
                    doc_app('{}\n'.format(ds_line))

                # If this is a blank line and we are not writing code
                # or if this is a comment line, skip.
                elif (not sline and not code_block) \
                    or sline.startswith(cls.COMMENT_START_WITH):
                    continue

                # Any other lines should be code to be inserted.
                elif insert_code:
                    if not code_block:
                        doc_app('.. code-block:: cf3\n\n')
                        code_block = True
                    doc_app(
                        '{}{}\n'.format(
                            ' ' * (cls.DOCSTRING_INDENT), line.rstrip()
                        )
                    )

        if doclines:
            with suppress(OSError), open(dst, 'w') as fd:
                fd.writelines(doclines)
                return True
        return False


    @classmethod
    def to_dir(cls, src, dst, insert_code=False):
        """Given a propanelib *src* directory, extract all the docstrings
        from the source files and save the result in *dst*.

        :param str src: Path to source code directory of a propanelib
                        project.
        :param str dst: Path to directory in which to save extracted
                        docstring files.

        :param bool insert_code: Shall the documented code also be
                                 included in the resulting document?
                                 Defaults to ``False``.

        """
        cf_files = [
            (p, p.replace(src, dst).replace(cls.EXT_CF, cls.EXT_RST))
            for p in sorted(fs.lstree(src, recursive=True))
            if p.endswith(cls.EXT_CF) and not os.path.isdir(p)
        ]

        if not cf_files:
            return

        fs.copytree(src, dst)
        for source, dest in cf_files:
            cls.extract(source, dest, insert_code)
        fs.rmdir(dst, recursive=True)


#
# Working environment management
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

class env(object):
    """Namespace for project's working environment management.

    :attribute ENVIRONMENT_DEFAULTS: Default environment values.

    """
    ENVIRONMENT_DEFAULTS = {
        'project': {
            'default_env': 'dev',
            'build_d': 'build',
            'src_d': 'src',
        },
        'doc': {
            'insert_code': True,
            'src_d': 'doc',
            'target': 'html',
        },
    }
    ENVIRONMENT_DEFAULTS['doc']['build_d'] = os.path.join(
        ENVIRONMENT_DEFAULTS['project']['build_d'], 'doc'
    )


    @classmethod
    def dmap(cls, callback, *mapping, recurse=False):
        """Apply *callack* to every item of *mapping*. If *recurse* is
        ``True``, *callback* will also be applied to any child mapping
        found.

        .. note:: This method will alter given *mapping* if called
                  *callback* does so.

        :param func callback: Function to be applied to the elements in
                              *mapping*.
        :param dict mapping: Dictionary to apply *callback* on. Multiple
                             may be given.
        :param bool recurse: Should *callback* also be applied to child
                             dictionaries? Defaults to ``False``.

        """
        for m in mapping:
            with suppress(AttributeError):
                for k, v in tuple(m.items()):
                    if recurse and isinstance(v, dict):
                        cls.dmap(callback, v, recurse)
                    else:
                        callback(m, k, v)


    @classmethod
    def load(cls, *pattern, use_defaults=False):
        """Load a environment file into a new namespace.

        :param str pattern: Pattern of environment files to load. Give
                            multiple patterns to load all matching files
                            in the same name space.

        :param bool use_defaults: Should returned environment be using
                                  default values as a base?

        :returns: Environment dictionary.
        :rtype: dict

        """
        environment = {}
        if use_defaults:
            environment = cls.ENVIRONMENT_DEFAULTS.copy()

        def _load_include(mapping, key, val):
            """Update given dictionary with given ``include`` directive
            item.

            An ``include`` directive is any dictionary key named
            ``include`` with a path or a list of paths for value. The
            file targeted by those paths should be a YAML environment
            file to be added to given *mapping*.

            This function will not loop over the dictionary and asumes
            *key* and *val* is an item part of it.

            :param dict mapping: Dictionary to look in and to be updated
                                 by the ``include`` directives.

            :param key: A key from *mapping*.
            :param value: A value from *mapping*.

            """
            if key == 'include':
                with suppress(KeyError):
                    del mapping[key]
                cls.update(mapping, cls.load(val))

            # Try to look for inclue directives if list of dict.
            with suppress(TypeError):
                cls.dmap(_load_include, *val, recurse=True)
        # end _load_include

        # Defaults may have include directives.
        cls.dmap(_load_include, environment, recurse=True)
        for path in fs.shexpand(pattern):
            loaded = {}
            with open(path, 'r') as fp:
                loaded = yaml.safe_load(fp)
                cls.dmap(_load_include, loaded, recurse=True)
            cls.update(environment, loaded)

        return environment


    @classmethod
    def update(cls, target, *mapping):
        """Merge given target dictionary with given *mapping* object.
        Unlike Python's dict.update() method, if the same key is present
        in both dictionaries and the value for this key is a dictionary,
        it will be updated instead of being replaced by the dictionary
        from the *mapping* object. All other data types will be replaced.

        For example::

          >>> d1 = {'baz': {'foo': 'foo'}, 'fizz': 'buzz'}
          >>> d2 = {'baz': {'bar': 'bar'}, 'fizz': 'fizzbuzz'}
          >>> env.update(d1, d2)
          >>> d1
          {'baz': {'foo': 'foo', 'bar': 'bar'}, 'fizz': 'fizzbuzz'}

        :param dict target: Dictionary to be updated.
        :param dict mapping: Dictionary to be merged. Multiple may be
                             given.

        """
        for m in mapping:
            with suppress(AttributeError):
                for k, v in tuple(m.items()):
                    if k in target and isinstance(v, dict):
                        cls.update(target[k], v)
                    else:
                        target[k] = deepcopy(v)


    @classmethod
    def update_context(cls, environment, *ctx):
        """Update Jinja2 context dictionary with useful elements from
        the project.

        :param dict environment: Current project environment.
        :param dict ctx: Context dictionary to be updated.

        """
        context_functions = (
            cls.context_add_project,
        )

        for c in ctx:
            for fn in context_functions:
                fn(environment, c)


    @classmethod
    def render_tree(cls, context, src, dst):
        """Run given *src* directories through the Jinja2 template engine
        and render the result in the *dst* folder.

        :param dict context: Context dictionary to pass to Jinja2.

        :param dict src: Dictionary of source directories to be rendered.
                         Keys of this dictionary should be paths relative
                         to the destination and values the original path
                         for the template files::

                           >>> src = {
                           ...   '.': '/path/to/foo',
                           ...   'bar': '/path/to/bar',
                           ... }

                          Files from ``/path/to/foo`` will be rendered in
                          ``dst/.`` while files from ``/path/to/bar``
                          will be in ``dst/bar``.

        """
        loader = {k: jinja2.FileSystemLoader(v) for k, v in src.items()}
        engine = jinja2.Environment(
            extensions = ['jinja2.ext.loopcontrols', ],
            loader = jinja2.PrefixLoader(loader),
            trim_blocks = True,
            lstrip_blocks = True
        )

        for name, path in src.items():
            fs.copytree(path, os.path.join(dst, name))

        for name in engine.list_templates():
            with open(os.path.join(dst, name), 'w') as fp:
                fp.write(engine.get_template(name).render(context))


    @classmethod
    def context_add_project(cls, environment, ctx):
        """Add project information from the environment into the context.

        :param dict environment: Current project environment.
        :param dict ctx: Context dictionary to be updated.

        """
        cls.update(
            ctx.setdefault('project', {}),
            environment.get('project', {})
        )


#
# Task definitions
# ----------------

ENVIRONMENT = env.load('env.conf', use_defaults=True)


#
# Project tasks
# ^^^^^^^^^^^^^

@task(name='clean')
def project_clean():
    """Clean project folder from built files."""
    build_d   = ENVIRONMENT['project']['build_d']
    src_d     = ENVIRONMENT['project']['src_d']
    build_log = os.path.join(build_d, '.build')

    patterns = [build_d, ]
    if os.path.exists(build_log):
        with open(build_log, 'r') as fp:
            patterns = [x for x in fp.read().splitlines() if x]
        patterns.append(build_log)

    lines = [x for x in fs.shexpand(patterns)]
    if lines:
        msg.write(msg.INFORMATION,
                  'Cleaning project', *sorted(lines, reverse=True))
    fs.rmtree(patterns)


_proj_build_help = {
    'environment': "Project environment to be built. Defaults to {}.".format(
        ENVIRONMENT.get('default_env', 'dev')
    ),
}
@task(project_clean, name='build', help=_proj_build_help)
def project_build(environment=ENVIRONMENT.get('default_env', 'dev')):
    """Build the project."""
    build_d   = ENVIRONMENT['project']['build_d']
    src_d     = ENVIRONMENT['project']['src_d']
    build_log = os.path.join(build_d, '.build')

    fs.copytree(src_d, build_d)

    proj_env = [
        x
        for x in ENVIRONMENT.get('environment', {})
        if x.get('name', '') == environment
    ][0]

    dirs = {
        '.': ENVIRONMENT['project']['src_d'],
    }

    context = {}
    with suppress(AttributeError):
        context = {
            k: v
            for k, v in proj_env.get('variables', {}).items()
        }
    env.update_context(ENVIRONMENT, context)

    rendered = [
        os.path.join(build_d, origine.replace(path, name))
        for name, path in dirs.items()
        for origine in fs.lstree(path, recursive=True)
    ]

    msg.write(msg.INFORMATION, 'Building project', *rendered)
    env.render_tree(context, dirs, build_d)

    with suppress(OSError), open(build_log, 'w') as fp:
        fp.write('\n'.join(rendered))


#
# Project task namespace
# """"""""""""""""""""""

ns_proj = Collection('proj')
ns_proj.add_task(project_build)
ns_proj.add_task(project_clean)

ns.add_collection(ns_proj)


#
# Documentation tasks
# ^^^^^^^^^^^^^^^^^^^

@task(name='clean')
def doc_clean():
    """Clean project folder from built documentation files."""
    patterns = [ENVIRONMENT['doc']['build_d'], ]

    lines = [x for x in fs.shexpand(patterns)]
    if lines:
        msg.write(msg.INFORMATION,
                  'Cleaning documentation', *sorted(lines, reverse=True))
    fs.rmtree(patterns)


_doc_build_help = {
    'target': "Targeted documentation format. Default to {}.".format(
        ENVIRONMENT['doc']['target']
    ),
    'code': "Insert documented code into documentation. Default to {}.".format(
        ENVIRONMENT['doc']['insert_code']
    ),
}
@task(doc_clean, name='build', help=_doc_build_help)
def doc_build(target=ENVIRONMENT['doc']['target'],
              code=ENVIRONMENT['doc']['insert_code']):
    """Build documentation using Sphinx."""
    build_d = ENVIRONMENT['doc']['build_d']
    out_d   = os.path.join(build_d, 'output', target)
    src_d   = os.path.join(build_d, ENVIRONMENT['project']['src_d'])

    msg.write(msg.INFORMATION, 'Building documentation')

    shutil.copytree(ENVIRONMENT['doc']['src_d'], build_d)
    docstring.to_dir(
        ENVIRONMENT['project']['src_d'],
        src_d,
        insert_code=code
    )

    run(
        'sphinx-build -b {target} {build_d} {out_d}'.format(
            **locals()
        )
    )


#
# Documentation tasks namespace
# """""""""""""""""""""""""""""

ns_doc = Collection('doc')
ns_doc.add_task(doc_build)
ns_doc.add_task(doc_clean)

ns.add_collection(ns_doc)


#
# Global tasks
# ^^^^^^^^^^^^

@task(project_build, doc_build, default=True)
def build():
    """Call all the build tasks to build the project."""
    msg.write(msg.INFORMATION, 'Done!')


@task(doc_clean, project_clean)
def clean():
    """Clean the whole project tree from built files."""
    patterns = [
        ENVIRONMENT['project']['build_d'],
    ]

    lines = [
        x
        for x in fs.lstree(patterns, recursive=True, include_path=True)
        if os.path.isdir(x)
    ]
    if lines:
        msg.write(msg.INFORMATION,
                  'Cleaning environment', *sorted(lines, reverse=True))
    msg.write(msg.INFORMATION, 'Done!')

    fs.rmdir(patterns, recursive=True)


ns.add_task(build)
ns.add_task(clean)

