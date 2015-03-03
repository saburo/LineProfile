# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LineProfile
                                 A QGIS plugin
 This plugin makes line profile
                             -------------------
        begin                : 2015-02-16
        copyright            : (C) 2015 by Kouki Kitajima
        email                : saburo@geology.wisc.edu
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load LineProfile class from file LineProfile.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .line_profile import LineProfile
    return LineProfile(iface)
