from PyQt4.QtGui import *
from PyQt4.QtCore import *
import logging


LOG = logging.getLogger(__name__)


class PolygonEnumeratorPlugin(QObject):
    """Enumerate the corners of polygons."""

    def __init__(self, labeltool):
        QObject.__init__(self)

        # Decorate the paint() method with our enumerating paint:
        from sloth.items import PolygonItem
        oldpaint = PolygonItem.paint

        def paint(self, painter, option, widget=None):
            oldpaint(self, painter, option, widget)
            for i, p in enumerate(self._polygon):
                painter.drawText(p, str(i))

        import functools
        functools.update_wrapper(paint, oldpaint)

        PolygonItem.paint = paint

    def action(self):
        return None
