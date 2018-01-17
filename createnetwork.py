# -*- coding: utf-8 -*-

"""
***************************************************************************
    createnetwork.py
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

from osgeo import gdal, ogr, gnm

from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFolderDestination
                      )

from processing.algs.gdal.GdalUtils import GdalUtils

from processing_gnm.gnmAlgorithm import GnmAlgorithm


class CreateNetwork(GnmAlgorithm):

    INPUT_LAYERS = "INPUT_LAYERS"
    TOLERANCE = "TOLERANCE"
    #~ FORMAT = "FORMAT"
    CRS = "CRS"
    NAME = "NAME"
    DESCRIPTION = "DESCRIPTION"
    RULES = "RULES"
    NETWORK = "NETWORK"

    def name(self):
        return "createnetwork"

    def displayName(self):
        return self.tr("Create network")

    def group(self):
        return self.tr("Network management")

    def groupId(self):
        return "management"

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMultipleLayers(self.INPUT_LAYERS,
                                                               self.tr("Layer to add to the network")))
        self.addParameter(QgsProcessingParameterNumber(self.TOLERANCE,
                                                       self.tr("Topology tolerance"),
                                                       QgsProcessingParameterNumber.Double,
                                                       0.0))
        #~ self.addParameter(QgsProcessingParameterString(self.FORMAT,
                                                       #~ self.tr("Network format"),
                                                       #~ "ESRI Shapefile"))
        self.addParameter(QgsProcessingParameterCrs(self.CRS,
                                                    self.tr("Network CRS"),
                                                    "ProjectCrs"))
        self.addParameter(QgsProcessingParameterString(self.NAME,
                                                       self.tr("Network name")))
        self.addParameter(QgsProcessingParameterString(self.DESCRIPTION,
                                                       self.tr("Network description"),
                                                       optional=True))
        self.addParameter(QgsProcessingParameterString(self.RULES,
                                                       self.tr("Network rules"),
                                                       multiLine=True,
                                                       optional=True))

        self.addParameter(QgsProcessingParameterFolderDestination(self.NETWORK,
                                                                  self.tr("Output directory")))

    def processAlgorithm(self, parameters, context, feedback):
        layers = layers = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)
        networkName = self.parameterAsString(parameters, self.NAME, context)
        #~ networkFormat = self.getParameterValue(self.NETWORK_FORMAT)

        if networkName == "":
            raise QgsProcessingException(self.tr("Network name can not be empty."))

        # hardcoded for now, as only file-based networks implemented
        driver = gdal.GetDriverByName("GNMFile")
        if driver is None:
            raise QgsProcessingException(self.tr("Can not initialize GNM driver."))

        # network metadata
        options = []
        options.append("net_srs={}".format(self.parameterAsCrs(parameters, self.CRS, context).authid()))
        options.append("net_name={}".format(networkName))
        options.append("net_description={}".format(self.parameterAsString(parameters, self.DESCRIPTION, context)))

        # create empty network dataset
        outputPath = self.parameterAsString(parameters, self.NETWORK, context)
        ds = driver.Create(outputPath, 0, 0, 0, gdal.GDT_Unknown, options)
        network = gnm.CastToNetwork(ds)
        if network is None:
            raise QgsProcessingException(self.tr("Can not initialize network dataset."))

        genericNetwork = gnm.CastToGenericNetwork(ds)
        if genericNetwork is None:
            raise QgsProcessingException(self.tr("Can not initialize generic network dataset."))

        # network created, now it is time to add layers to it
        hasPointLayer = False
        hasLineLayer = False
        importedLayers = []
        for layer in layers:
            layerSource = GdalUtils.ogrConnectionString(layer.source(), context).strip('"')
            layerDs = gdal.OpenEx(layerSource, gdal.OF_VECTOR)
            if layerDs is None:
                raise QgsProcessingException(self.tr("Can not open dataset {}.".format(layerSource)))

            # we assume that each dataset has only one layer in it
            ogrLayer = layerDs.GetLayerByIndex(0)
            if ogrLayer is None:
                raise QgsProcessingException(self.tr("Can not fetch layer 0 from the dataset {}.".format(layerSource)))

            # import layer into network
            layerName = ogrLayer.GetName()
            networLayer = network.CopyLayer(ogrLayer, layerName)
            if networLayer is None:
                raise QgsProcessingException(
                    self.tr("Could not import layer 0 from the dataset {} into the network.".format(layerSource)))

            importedLayers.append(networLayer.GetName())

            geometryType = networLayer.GetGeomType()
            if geometryType == ogr.wkbPoint:
                hasPointLayer = True
            elif geometryType == ogr.wkbLineString:
                hasLineLayer = True

            layerDs = None

        # add rules
        rules = self.parameterAsString(parameters, self.RULES, context)
        if rules != "":
            for r in rules.split("\n"):
                result = genericNetwork.CreateRule(r)
                if result != 0:
                    raise QgsProcessingException(self.tr("Can not create rule '{}'.".format(r)))

        # warn user if some layers are missing
        if not hasPointLayer:
            raise QgsProcessingException(
                self.tr("No point layers were imported. We will not be able to build network topology."))
        elif not hasLineLayer:
            raise QgsProcessingException(
                self.tr("No line layers were imported. We will not be able to build network topology."))

        # create network topology
        tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)
        result = genericNetwork.ConnectPointsByLines(
            importedLayers, tolerance, 1.0, 1.0, gnm.GNM_EDGE_DIR_BOTH)
        if result != 0:
            raise QgsProcessingException(self.tr("Can not build network topology."))

        # close all datasets
        genericNetwork = None
        network = None
        ds = None

        return {self.NETWORK: outputPath}
