# -*- coding: utf-8 -*-

"""
***************************************************************************
    gnmprovider.py
    ---------------------
    Date                 : February 2017
    Copyright            : (C) 2017 by Alexander Bruy
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
__copyright__ = '(C) 2017, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig

from processing_gnm.createnetwork import CreateNetwork


class GnmProvider(AlgorithmProvider):

    def __init__(self):
        super().__init__()

        self.activate = False

        self.alglist = []
        self.alglist = [CreateNetwork()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)

    def unload(self):
        AlgorithmProvider.unload(self)

    def id(self):
        return 'GDAL GNM'

    def name(self):
        return 'GDAL GNM'

    def icon(self):
        return AlgorithmProvider.icon(self)

    def _loadAlgorithms(self):
        self.algs = self.alglist
