#!/usr/bin/python

# --------------------------------------------------------------------------------------
#
#    cartesianStemPlot: - Inkscape extension to plot discrete data of one independent variable
#
#    Copyright (C) 2017 by Fernando Moura
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# --------------------------------------------------------------------------------------

import math
import os

import numpy

import inkscapeMadeEasy.inkscapeMadeEasy_Base as inkBase
import inkscapeMadeEasy.inkscapeMadeEasy_Draw as inkDraw
import inkscapeMadeEasy.inkscapeMadeEasy_Plot as inkPlot


# heaviside function
def u(x):
    if x < 0:
        return 0.0
    else:
        return 1.0


# rectangular Pulse
def rectPulse(x, amplitude=1.0, length=1.0, offset=0.0, delay=0.0):
    return amplitude * (u(x - delay) - u(x - length - delay)) + offset


# square wave, with amplitude -A/2 to A/2, and given period
def squareWave(x, amplitude=1.0, offset=0, period=1.0, delay=0.0):
    return rectPulse((x % period), amplitude, period / 2.0, offset=-amplitude / 2.0 + offset, delay=delay)


# ---------------------------------------------
class DiscretePlot(inkBase.inkscapeMadeEasy):
    def __init__(self):
        inkBase.inkscapeMadeEasy.__init__(self)

        self.arg_parser.add_argument("--tab", type=str, dest="tab", default="object")
        self.arg_parser.add_argument("--subtab_axis", type=str, dest="subtab_axis", default="object")
        self.arg_parser.add_argument("--subTab_help", type=str, dest="subTab_help", default="object")

        self.arg_parser.add_argument("--Values", type=str, dest="yValues", default='0 1 0 1 1')

        self.arg_parser.add_argument("--filePath", type=str, dest="filePath", default='')
        self.arg_parser.add_argument("--charSeparator", type=str, dest="charSeparator", default=' ')
        self.arg_parser.add_argument("--skipHeader", type=self.bool, dest="skipHeader", default=False)
        self.arg_parser.add_argument("--headerSize", type=int, dest="headerSize", default=0)

        self.arg_parser.add_argument("--ZeroPoint", type=int, dest="ZeroPoint", default='2')
        self.arg_parser.add_argument("--generalAspectFactor", type=float, dest="generalAspectFactor", default=1.0)
        self.arg_parser.add_argument("--stemAspectFactor", type=float, dest="stemAspectFactor", default=1.0)
        self.arg_parser.add_argument("--useElipsis", type=self.bool, dest="useEllipsis", default=False)
        self.arg_parser.add_argument("--drawAxis", type=self.bool, dest="drawAxis", default=False)

        self.arg_parser.add_argument("--xLabel", type=str, dest="xLabel", default='')
        self.arg_parser.add_argument("--xGrid", type=self.bool, dest="xGrid", default=True)
        self.arg_parser.add_argument("--xTicks", type=self.bool, dest="xTicks", default=False)
        self.arg_parser.add_argument("--xTickStep", type=int, dest="xTickStep", default=1)
        self.arg_parser.add_argument("--xScale", type=float, dest="xScale", default='5')
        self.arg_parser.add_argument("--xExtraText", type=str, dest="xExtraText", default='')

        self.arg_parser.add_argument("--yLabel", type=str, dest="yLabel", default='')
        self.arg_parser.add_argument("--yGrid", type=self.bool, dest="yGrid", default=True)
        self.arg_parser.add_argument("--yTicks", type=self.bool, dest="yTicks", default=False)
        self.arg_parser.add_argument("--yTickStep", type=float, dest="yTickStep", default=1)
        self.arg_parser.add_argument("--yScale", type=float, dest="yScale", default='10')
        self.arg_parser.add_argument("--yExtraText", type=str, dest="yExtraText", default='')

        self.arg_parser.add_argument("--yLimitsFlag", type=self.bool, dest="yLimitsFlag", default=False)
        self.arg_parser.add_argument("--yMin", type=float, dest="yMin", default='0.0')
        self.arg_parser.add_argument("--yMax", type=float, dest="yMax", default='0.0')

        self.arg_parser.add_argument("--markColor", type=str, dest="markColorOption", default='black')
        self.arg_parser.add_argument("--colorPickerMark", type=str, dest="colorPickerMark", default='0')

        self.arg_parser.add_argument("--lineColor", type=str, dest="lineColorOption", default='black')
        self.arg_parser.add_argument("--colorPickerLine", type=str, dest="colorPickerLine", default='0')

    def effect(self):

        so = self.options

        # sets the position to the viewport center, round to next 10.
        position = [self.svg.namedview.center[0], self.svg.namedview.center[1]]
        position[0] = int(math.ceil(position[0] / 10.0)) * 10
        position[1] = int(math.ceil(position[1] / 10.0)) * 10

        # root_layer = self.current_layer
        root_layer = self.document.getroot()
        # root_layer = self.getcurrentLayer()

        # check if file exists and extract coords data

        if os.path.isfile(so.filePath):

            if so.skipHeader:
                data = numpy.loadtxt(so.filePath, delimiter=so.charSeparator, skiprows=so.headerSize)
            else:
                data = numpy.loadtxt(so.filePath, delimiter=so.charSeparator)

            YValuesVector = []
            minValues = []
            maxValues = []

            for i in range(0, data.shape[1]):
                YValuesVector.append(data[:, i].tolist())
                minValues.append(min(data[:, i].tolist()))
                maxValues.append(max(data[:, i].tolist()))

            Ylimits = [min(min(minValues), 0), max(max(maxValues), 0)]
        else:
            # create vector of inputs
            YValuesVector = [[float(column) for column in so.yValues.replace(',', ' ').split()]]  # list of list
            Ylimits = [min(min(YValuesVector[0]), 0), max(max(YValuesVector[0]), 0)]

        nSamples = len(YValuesVector[0])
        if nSamples < so.ZeroPoint:
            so.ZeroPoint = nSamples
        xData = list(range(min(-(so.ZeroPoint - 1), 0), max(nSamples - (so.ZeroPoint - 1) - 1, 0) + 1))

        # limits
        EstraDistX = 2

        if so.yLimitsFlag:
            # check if limits are valid
            if so.yMin >= so.yMax:
                self.displayMsg('Error: yMin and yMax are invalid.')
                return 0
            Ylimits = [min(0, so.yMin), max(0, so.yMax)]

            # block limits
            for i in range(len(YValuesVector)):
                if sum(y > Ylimits[1] for y in YValuesVector[i]) > 0:
                    inkDraw.text.write(self, 'Some Yvalues are greater than yMax.\n Clipping values... PLEASE CHECK YOUR PLOT!',
                                       [position[0], position[1] + 8], root_layer, fontSize=5)
                if sum(y < Ylimits[0] for y in YValuesVector[i]) > 0:
                    inkDraw.text.write(self, 'Some Yvalues are smaller than yMin.\n Clipping values... PLEASE CHECK YOUR PLOT!',
                                       [position[0], position[1] + 16], root_layer, fontSize=5)

                YValuesVector[i] = [min(y, Ylimits[1]) for y in YValuesVector[i]]
                YValuesVector[i] = [max(y, Ylimits[0]) for y in YValuesVector[i]]

        # line style
        lineWidthDiscrete = 2 * so.generalAspectFactor * min(so.xScale, so.yScale) * so.stemAspectFactor / 40.0
        textSize = 8 * lineWidthDiscrete
        # sets colors. See inkDraw.color class for instructions.
        markerColor = inkDraw.color.parseColorPicker(so.markColorOption, so.colorPickerMark)
        lineColor = inkDraw.color.parseColorPicker(so.lineColorOption, so.colorPickerLine)

        nameMarkerDot = inkDraw.marker.createDotMarker(self, 'DotMDiscreteTime', RenameMode=2, scale=0.3 * so.stemAspectFactor,
                                                       strokeColor=markerColor, fillColor=markerColor)
        lineStyleDiscrete = inkDraw.lineStyle.set(lineWidthDiscrete, markerEnd=nameMarkerDot, lineColor=lineColor)

        for i in range(len(YValuesVector)):
            if so.drawAxis:
                flagDrawAxis = True
            else:
                if i == 0:
                    flagDrawAxis = True
                else:
                    flagDrawAxis = False

            [axisObj, limits, origin] = inkPlot.plot.stem(self, root_layer, xData, YValuesVector[i], position, xLabel=so.xLabel, yLabel=so.yLabel,
                                                          ylog10scale=False, xTicks=so.xTicks, yTicks=so.yTicks, xTickStep=so.xTickStep,
                                                          yTickStep=so.yTickStep, xScale=so.xScale, yScale=so.yScale, xExtraText=so.xExtraText,
                                                          yExtraText=so.yExtraText, xGrid=so.xGrid, yGrid=so.yGrid,
                                                          generalAspectFactorAxis=so.generalAspectFactor, lineStylePlot=lineStyleDiscrete,
                                                          forceXlim=None, forceYlim=Ylimits, drawAxis=flagDrawAxis, ExtraLengthAxisX=EstraDistX,
                                                          ExtraLengthAxisY=0.0)

            if so.useEllipsis:
                ypos = (-(Ylimits[1] + Ylimits[0]) / 2.0) * (so.yScale / so.yTickStep) + position[1]
                inkDraw.text.latex(self, axisObj, '$\ldots$', [(xData[0] - 1.0) * (so.xScale / so.xTickStep) + position[0], ypos], fontSize=textSize,
                                   refPoint='cc')
                inkDraw.text.latex(self, axisObj, '$\ldots$', [(xData[-1] + 1.0) * (so.xScale / so.xTickStep) + position[0], ypos], fontSize=textSize,
                                   refPoint='cc')


if __name__ == '__main__':
    plot = DiscretePlot()
    plot.run()
