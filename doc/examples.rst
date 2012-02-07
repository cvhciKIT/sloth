.. highlight:: python

========
Examples
========

Adding every nth image to label file
------------------------------------

This can be achieved by a combination of ``find`` and ``awk``::

    find shot01/ -iname "*.png" | sort | awk 'NR%5==1' | xargs sloth appendfiles shot01.json


