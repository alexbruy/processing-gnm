# -*- coding: utf-8 -*-

"""
***************************************************************************
    connectivitytreepoint.py
    ---------------------
    Date                 : March 2017
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
__date__ = 'March 2017'
__copyright__ = '(C) 2017, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from osgeo import gdal, gnm, ogr

from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsGeometry,
                       QgsFeature,
                       QgsFields)

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import (ParameterFile,
                                        ParameterNumber,
                                        ParameterString)

from processing.core.outputs import OutputVector

from processing.algs.gdal.GdalUtils import GdalUtils


class ConnectivityTreePoint(GeoAlgorithm):

    NETWORK = 'NETWORK'
    START_POINT = 'START_POINT'
    BLOCKED_POINTS = 'BLOCKED_POINTS'
    CONNECTIVITY_TREE = 'CONNECTIVITY_TREE'

    def defineCharacteristics(self):
        self.name = 'Connectivity tree (from point)'
        self.group = 'Network analysis'

        self.addParameter(ParameterFile(
            self.NETWORK,
            self.tr('Directory with network'),
            isFolder=True,
            optional=False))
        self.addParameter(ParameterNumber(
            self.START_POINT,
            self.tr('GFID of the start node (value of the "gnm_fid" field)')))
        self.addParameter(ParameterString(
            self.BLOCKED_POINTS,
            self.tr('Comma-separated GFIDs of the blocked nodes'),
            '',
            optional=True))

        self.addOutput(OutputVector(
            self.CONNECTIVITY_TREE,
            self.tr('Connectivity tree')))

    def processAlgorithm(self, feedback):
        networkPath = self.getParameterValue(self.NETWORK)
        gfidStart = self.getParameterValue(self.START_POINT)
        gfidsBlocked = self.getParameterValue(self.BLOCKED_POINTS)
        outputPath = self.getOutputValue(self.CONNECTIVITY_TREE)

        if gfidsBlocked is not None:
            gfidsBlocked = [int(gfid.strip()) for gfid in gfidsBlocked.split(',')]

        if gfidStart in gfidsBlocked:
            raise GeoAlgorithmExecutionException(
                self.tr('Start point can not be blocked.'))

        # load network
        ds = gdal.OpenEx(networkPath)
        network = gnm.CastToGenericNetwork(self.NETWORK_DS)
        if network is None:
            raise GeoAlgorithmExecutionException(
                self.tr('Can not open generic network dataset.'))

        # block nodes if necessary
        if gfidsBlocked is not None:
            for gfid in gfidsBlocked:
                network.ChangeBlockState(gfid, True)

        # calculate shortest paths
        layer = network.GetPath(gfidStart, -1, gnm.GATConnectedComponents)

        # unblock previously blocked nodes
        if gfidsBlocked is not None:
            for gfid in gfidsBlocked:
                network.ChangeBlockState(gfid, False)

        if layer is None:
            raise GeoAlgorithmExecutionException(
                self.tr('Error occured during connectivity tree calculation.'))

        if layer.GetFeatureCount() == 0:
            feedback.pushInfo(
                self.tr('Start node has no connections with other nodes.'))

        # move features to the output layer
        if outputPath.startswith(('memory:', 'postgis:', 'spatialite:')):
            networkCrs = network.GetProjectionRef()
            crs = QgsCoordinateReferenceSystem(networkCrs)
            # TODO: copy fields
            fields = QgsFields()
            writer = self.getOutputFromName(
                self.OUTPUT_LAYER).getVectorWriter(
                    fields,
                    QgsWkbTypes.LineString,
                    crs)

            feat = QgsFeature()
            geom = QgsGeometry()

            layer.ResetReading()
            f = layer.GetNextFeature()
            while f is not None:
                wkbGeom = f.GetGeometryRef().ExportToWkb(ogr.wkbNDR)
                geom.fromWkb(wkb)
                feat.setGeometry(geom)
                writer.addFeature(feat)
                f = layer.GetNextFeature()

            del writer
        else:
            driverName = GdalUtils.getVectorDriverFromFileName(outputPath)
            driver = gdal.GetDriverByName(driverName)
            if driver is None:
                raise GeoAlgorithmExecutionException(
                    self.tr('Can not initialize {} driver'.format(driverName)))

            outDs = driver.Create(outputPath, 0, 0, 0, gdal.GDT_Unknown, None)
            if outDs is None:
                raise GeoAlgorithmExecutionException(
                    self.tr('Can not create output file {}'.format(outputPath)))

            layerName = os.path.splitext(os.path.baseName(outputPath))[0]
            res = outDs.CopyLayer(layer, layerName)
            if res is None:
                raise GeoAlgorithmExecutionException(
                    self.tr('Can not write data to the output file {}'.format(outputPath)))

            outDs = None

        network.ReleaseResultSet(layer)
        network = None
        ds = None
