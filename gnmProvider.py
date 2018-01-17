# -*- coding: utf-8 -*-

"""
***************************************************************************
    gnmprovider.py
    ---------------------
    Date                 : February 2017
    Copyright            : (C) 2017-2018 by Alexander Bruy
    Email                : alexander dot bruy at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alexander Bruy'
__date__ = 'February 2017'
__copyright__ = '(C) 2017-2018, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import QgsProcessingProvider

from processing.core.ProcessingConfig import ProcessingConfig, Setting

from processing_gnm.createnetwork import CreateNetwork
from processing_gnm.removenetwork import RemoveNetwork
from processing_gnm.shortestpathpointtopoint import ShortestPathPointToPoint
from processing_gnm.connectivitytreepoint import ConnectivityTreePoint

from processing_gnm import gnmUtils

pluginPath = os.path.dirname(__file__)


class GnmProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()
        self.algs = []

    def id(self):
        return "gdalgmn"

    def name(self):
        return "GDAL GNM"

    def icon(self):
        return QIcon(os.path.join(pluginPath, "icons", "gnm.svg"))

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()
        ProcessingConfig.addSetting(Setting(self.name(),
                                            gnmUtils.GDALGNM_ACTIVE,
                                            self.tr("Activate"),
                                            False))

        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True

    def unload(self):
        ProcessingConfig.removeSetting(gnmUtils.GDALGNM_ACTIVE)

    def isActive(self):
        return ProcessingConfig.getSetting(gnmUtils.GDALGNM_ACTIVE)

    def setActive(self, active):
        ProcessingConfig.setSettingValue(gnmUtils.GDALGNM_ACTIVE, active)

    def getAlgs(self):
        algs = [CreateNetwork(),
                RemoveNetwork(),
                ShortestPathPointToPoint(),
                ConnectivityTreePoint()
               ]

        return algs

    def loadAlgorithms(self):
        self.algs = self.getAlgs()
        for a in self.algs:
            self.addAlgorithm(a)

    def tr(self, string, context=''):
        if context == "":
            context = "GnmProvider"
        return QCoreApplication.translate(context, string)

