# -*- coding: utf-8 -*-

"""
***************************************************************************
    shortestpathpointtopoint.py
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

from osgeo import gdal, gnm, ogr

from qgis.PyQt.QtCore import QVariant

from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsGeometry,
                       QgsFeature,
                       QgsFields,
                       QgsField,
                       QgsWkbTypes,
                       QgsFeatureSink,
                       QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSink,
                       )

from processing_gnm.gnmAlgorithm import GnmAlgorithm


class ShortestPathPointToPoint(GnmAlgorithm):

    NETWORK = "NETWORK"
    PATHS_NUMBER = "PATHS_NUMBER"
    START_POINT = "START_POINT"
    END_POINT = "END_POINT"
    BLOCKED_POINTS = "BLOCKED_POINTS"
    SHORTEST_PATHS = "SHORTEST_PATHS"

    def name(self):
        return "shortestpathpointtopoint"

    def displayName(self):
        return self.tr("Shortest paths (point to point)")

    def group(self):
        return self.tr("Network analysis")

    def groupId(self):
        return "analysis"

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(self.NETWORK,
                                                     self.tr("Network"),
                                                     QgsProcessingParameterFile.Folder))
        self.addParameter(QgsProcessingParameterNumber(self.PATHS_NUMBER,
                                                       self.tr("Number of paths to calculate"),
                                                       QgsProcessingParameterNumber.Integer,
                                                       1))
        self.addParameter(QgsProcessingParameterNumber(self.START_POINT,
                                                       self.tr("GFID of the start node"),
                                                       QgsProcessingParameterNumber.Integer,
                                                       0))
        self.addParameter(QgsProcessingParameterNumber(self.END_POINT,
                                                       self.tr("GFID of the end node"),
                                                       QgsProcessingParameterNumber.Integer,
                                                       0))
        self.addParameter(QgsProcessingParameterString(self.BLOCKED_POINTS,
                                                       self.tr("Comma-separated GFIDs of the blocked nodes"),
                                                       "",
                                                       optional=True))

        self.addParameter(QgsProcessingParameterFeatureSink(self.SHORTEST_PATHS,
                                                            self.tr('Shortest path(s)'),
                                                            QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):
        gfidStart = self.parameterAsInt(parameters, self.START_POINT, context)
        gfidEnd = self.parameterAsInt(parameters, self.END_POINT, context)
        gfidsBlocked = self.parameterAsString(parameters, self.BLOCKED_POINTS, context)

        if gfidStart == gfidEnd:
            raise QgsProcessingException(self.tr("Start and end points should be different."))

        if gfidsBlocked != "":
            gfidsBlocked = [int(gfid.strip()) for gfid in gfidsBlocked.split(",")]

            if gfidStart in gfidsBlocked:
                raise QgsProcessingException(self.tr("Start point can not be blocked."))

            if gfidEnd in gfidsBlocked:
                raise QgsProcessingException(self.tr("End point can not be blocked."))
        else:
            gfidsBlocked = None

        # load network
        ds = gdal.OpenEx(self.parameterAsString(parameters, self.NETWORK, context))
        network = gnm.CastToGenericNetwork(ds)
        if network is None:
            raise QgsProcessingException(self.tr("Can not open generic network dataset."))

        # block nodes if necessary
        if gfidsBlocked is not None:
            for gfid in gfidsBlocked:
                network.ChangeBlockState(gfid, True)

        # calculate shortest paths
        pathsNumber = self.parameterAsInt(parameters, self.PATHS_NUMBER, context)
        if pathsNumber == 1:
            layer = network.GetPath(gfidStart, gfidEnd, gnm.GATDijkstraShortestPath)
        else:
            options = ['num_paths={}'.format(pathsNumber)]
            layer = network.GetPath(gfidStart, gfidEnd, gnm.GATKShortestPath, options)

        # unblock previously blocked nodes
        if gfidsBlocked is not None:
            for gfid in gfidsBlocked:
                network.ChangeBlockState(gfid, False)

        if layer is None:
            raise QgsProcessingException(self.tr("Error occured during shortest path calculation."))

        if layer.GetFeatureCount() == 0:
            feedback.pushInfo(self.tr("There is no path from the start point to the end point."))

        # copy features to the output layer
        networkCrs = network.GetProjectionRef()
        crs = QgsCoordinateReferenceSystem(networkCrs)

        fields = QgsFields()
        fields.append(QgsField("gfid", QVariant.Int, "", 10, 0))
        fields.append(QgsField("ogrlayer", QVariant.String, "", 254))
        fields.append(QgsField("path_num", QVariant.Int, "", 10, 0))
        fields.append(QgsField("type", QVariant.String, "", 254))

        (sink, dest_id) = self.parameterAsSink(parameters, self.SHORTEST_PATHS, context,
                                               fields, QgsWkbTypes.LineString, crs)

        feat = QgsFeature()
        feat.setFields(fields)
        geom = QgsGeometry()

        layer.ResetReading()
        f = layer.GetNextFeature()
        while f is not None:
            g = f.GetGeometryRef()
            if g.GetGeometryType() == ogr.wkbLineString:
                wkb = g.ExportToWkb()
                geom.fromWkb(wkb)
                feat.setGeometry(geom)
                feat["gfid"] = f.GetFieldAsInteger64(0)
                feat["ogrlayer"] = f.GetFieldAsString(1)
                feat["path_num"] = f.GetFieldAsInteger64(2)
                feat["type"] = f.GetFieldAsString(3)
                sink.addFeature(feat, QgsFeatureSink.FastInsert)
            f = layer.GetNextFeature()

        network.ReleaseResultSet(layer)
        network = None
        ds = None

        return {self.SHORTEST_PATHS: dest_id}
