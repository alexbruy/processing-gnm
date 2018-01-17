# -*- coding: utf-8 -*-

"""
***************************************************************************
    gnmproviderplugin.py
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

from qgis.core import QgsApplication

from processing_gnm.gnmProvider import GnmProvider


class GnmProviderPlugin:

    def __init__(self):
        self.provider = GnmProvider()

    def initGui(self):
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
