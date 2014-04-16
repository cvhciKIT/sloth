.. highlight:: python

==================
Installation Guide
==================

Before you can install Sloth, make sure that you have all the prerequisites installed.

Prerequisites
=============

Sloth is implemented in `Python`_ and `PyQt4`_, so it needs both.  It further depends on 
either `PIL`_ or okapy for image loading.

.. _Python: http://www.python.org
.. _PyQt4:  http://www.riverbankcomputing.co.uk/software/pyqt/intro
.. _PIL:    http://www.pythonware.com/products/pil/

To use okapy, make sure to make its modules known to python, e.g. add
<okapibuild>/python/ to the PYTHONPATH environment variable::

     export PYTHONPATH=<okapibuild>/python/:$PYTHONPATH

For compiling the docs, `Python Sphinx`_ is needed.

.. _Python Sphinx: http://pypi.python.org/pypi/Sphinx


Installing Sloth
================

Run with administrator priviledges::

    python setup.py install


