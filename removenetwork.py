# -*- coding: utf-8 -*-

"""
***************************************************************************
    removenetwork.py
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

from osgeo import gdal

from qgis.core import QgsProcessingParameterFile, QgsProcessingOutputNumber

from processing_gnm.gnmAlgorithm import GnmAlgorithm

class RemoveNetwork(GnmAlgorithm):

    NETWORK = "NETWORK"
    RESULT = "RESULT"

    def name(self):
        return "removenetwork"

    def displayName(self):
        return self.tr("Remove network")

    def group(self):
        return self.tr("Network management")

    def groupId(self):
        return "management"

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(self.NETWORK,
                                                     self.tr("Network to remove"),
                                                     QgsProcessingParameterFile.Folder))
        self.addOutput(QgsProcessingOutputNumber(self.RESULT,
                                                 self.tr("Result")))

    def processAlgorithm(self, parameters, context, feedback):
        driver = gdal.GetDriverByName("GNMFile")
        if driver is None:
            raise QgsProcessingException(self.tr("Can not initialize GNM driver."))

        result = driver.Delete(self.parameterAsString(parameters, self.NETWORK, context))

        return {self.RESULT: result}
