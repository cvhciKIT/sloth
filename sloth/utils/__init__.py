import numpy as np
import random
import colorsys
from PyQt4.QtGui import QImage, qRgb
from sloth.core.exceptions import NotImplementedException


gray_color_table = [qRgb(i, i, i) for i in range(256)]


def toQImage(im, copy=False):
    if im is None:
        return QImage()

    if im.dtype == np.uint8:
        if len(im.shape) == 2:
            qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_Indexed8)
            qim.setColorTable(gray_color_table)
            return qim.copy() if copy else qim

        elif len(im.shape) == 3:
            if im.shape[2] == 3:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_RGB888)
                return qim.copy() if copy else qim
            elif im.shape[2] == 4:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_ARGB32)
                return qim.copy() if copy else qim
    raise NotImplementedException('no conversion to QImage implemented for given image type (depth: %s, shape: %s)' %
                                  (im.dtype, im.shape))


def gen_colors(s=0.99, v=0.99, h=None, color_space='rgb', _golden_ratio_conjugate=0.618033988749895):
    """A generator for random colors such that adjacent colors are as distinct as possible.

    Parameters
    ----------
    s: float
        saturation
    v: float
        value
    h: float (optional, default: random)
        initial hue
    color_space: string (optional, default: "rgb")
        the target color space, one of "rgb", "hsv"

    Returns
    -------
    A generator for tuples of floats (c1, c2, c3).
    """
    # see http://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/

    if color_space.lower() == 'rgb':
        cs_convert = colorsys.hsv_to_rgb
    elif color_space.lower() == 'hsv':
        cs_convert = lambda *args: args
    else:
        raise RuntimeError("invalid color_space parameter: %s" % color_space)

    if h is None:
        h = random.random()
    while True:
        h += _golden_ratio_conjugate
        h %= 1
        yield cs_convert(h, s, v)