propanelib
==========

*propanelib* is a library of promise `bodies
<https://docs.cfengine.com/docs/master/guide-language-concepts-bodies.html>`_
for `CFEngine 3`_.

CFEngine is a configuration management and automation framework that
lets you securely manage your IT infrastructure. If you don't know yet
about CFEngine, you can take a look at its `documentation
<https://docs.cfengine.com/latest/guide-introduction.html>`_ to get a
first grasp of it.

The goal of *propanelib* is to provide a set of re-usable promise bodies
to drive the development of your configuration policies.


.. _CFEngine 3: https://cfengine.com


Development
-----------

*propanelib* make use of various Python 3 utilities to drive its
development. If you wish to bring some changes to the project and
build it, you'll need to set up your working environment first.

Make sure to have `Python 3`_ in version *3.4* or later installed on
your system. If you are running Fedora or a Red Hat based Linux system,
you can run the following:

  .. code-block:: console

    # yum install python3

On the other hand if you are using a Debian based system, run the
following:

  .. code-block:: console

    # apt-get install python3

For any other system, you can find installation instructions on the
website of the Python project.


.. _Python 3: https://www.python.org/


Virtual environment
^^^^^^^^^^^^^^^^^^^

In order to keep your system clear from the development tools needed
for the project, it is advised to set up a Python 3 `virtual
environment <Python 3 venv_>`_.

Go to the project directory and run the following:

  .. code-block:: console

    $ pyvenv pyenv

This will created a directory named ``pyenv`` in the current folder in
which you will find a new Python 3 environment completely separated
from your system.

To activate this environment, you can enter the following command:

  .. code-block:: console

    $ source ./pyenv/bin/activate
    (pyenv)$

When a command should be entered within the virtual environment, we
use the following ``(pyenv)$``  prompt in console examples.


.. _Python 3 venv: https://docs.python.org/3/library/venv.html#venv-def


Installation requirements
^^^^^^^^^^^^^^^^^^^^^^^^^

All the utilities required to build or ease project's development are
listed in the ``requirements.txt`` file. Within an activated virtual
environment, run the following to install the required tools:

  .. code-block:: console

    (pyenv)$ pip install -r requirements.txt

This file will be updated each time a new version of an utility is
available or depending on the needs. Be sure to re-run this command
each time you notice a change to the ``requirements.txt`` file.


Invoke tasks
^^^^^^^^^^^^

Building the project involves many different tasks. To ease the
operation, needed actions needed are being put together in the
``tasks.py`` file and ran using the `Invoke`_ tool as simple shell
commands.


.. _Invoke: http://www.pyinvoke.org/


Licensing
---------

This software project is provided under the licensing terms of the
MIT License stated in the file ``LICENSE.rst``.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

