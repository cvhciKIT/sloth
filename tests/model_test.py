#!/usr/bin/env python
import os, sys
from PyQt4.QtGui import QApplication
from sloth.gui import MainWindow
from sloth.core.labeltool import LabelTool
from sloth import APP_NAME, ORGANIZATION_NAME, ORGANIZATION_DOMAIN
from pymodeltest.modeltest import ModelTest

SAMPLE_DATA = os.path.join(os.path.dirname(__file__), 'data', 'example1_labels.json')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setOrganizationDomain(ORGANIZATION_DOMAIN)
    app.setApplicationName(APP_NAME)

    labeltool = LabelTool()
    if len(sys.argv) < 2:
        sys.argv.append(SAMPLE_DATA)
    labeltool.execute_from_commandline(sys.argv)
    labeltool.modeltest = ModelTest(labeltool._model, labeltool)

    wnd = MainWindow(labeltool)
    labeltool._mainwindow = wnd
    wnd.show()

    sys.exit(app.exec_())
