import os
import numpy as np
import pysal as ps
import pandas as pd
import geopandas as gp

from math import pi
import matplotlib.pyplot as plt

from shapely.geometry.multipolygon import MultiPolygon

roundTol=3


def write_header_styles(fstream):
    fstream.write("\n<style>\n")
    fstream.write("table { font-family: arial, sans-serif; border-collapse: collapse; width: 100%; }\n")
    fstream.write("td, th { border: 1px solid #dddddd; text-align: left; padding: 8px; }\n")
    fstream.write("tr:nth-child(even) { background-color: #dddddd; }\n")
    fstream.write("mycolor {#ff0000}\n")
    fstream.write("</style>\n\n")


def generic_shapefile_report(outputName, dataFrame=None, shapefileName=None, idColumn=None, voteColumns=None, electionDicts=None):
    if dataFrame is not None:
        outputName = outputName.split('.')[0] + '.html'

        with open(outputName, "w") as f:
            f.write("<html>\n")
            write_header_styles(f)

            f.write("<body>\n")
            f.write(f"<h1 width:100%> Report on {dataFrame[0]}</h1>\n")

            numUnits = len(dataFrame[1])
            numMultiUnits = sum([1 for x in dataFrame[1]["geometry"] if type(x) == MultiPolygon])
            neighbors = ps.weights.Rook.from_dataframe(dataFrame[1], geom_col="geometry").neighbors
            numNbrs = np.array([float(len(x)) for x in neighbors.values()])
            avgNbrs, maxNbrs, minNbrs = np.round(np.mean(numNbrs), roundTol), max(numNbrs), min(numNbrs)

            numUnitsInsideUnits = sum([1 for x in neighbors.keys() if len(neighbors[x]) == 1])
            numIslands = sum([1 for x in neighbors.keys() if len(neighbors[x]) == 0])
            areas = np.round(np.array([float(x.area) for x in dataFrame[1]["geometry"]]), roundTol)
            perims = np.round(np.array([float(x.length) for x in dataFrame[1]["geometry"]]), roundTol)
            maxArea, minArea, avgArea = max(areas), min(areas), np.round(np.mean(areas), roundTol)
            maxPerim, minPerim, avgPerim = max(perims), min(perims), np.round(np.mean(perims), roundTol)
            polsbyPopper = np.round(4.0 * pi * areas / (perims**2), roundTol)
            avgPolsPop, maxPolsPop, minPolsPop = np.round(np.mean(polsbyPopper), roundTol), max(polsbyPopper), min(polsbyPopper)

            f.write(f"<h2 width:100%> Geometry: </h2>\n")
            f.write("<ul>\n")
            f.write(f"<li>{numUnits} units</li>\n")
            f.write(f"<li>{numIslands} disconnected units</li>\n")
            f.write(f"<li>{numMultiUnits} multiply connected or island-containing units</li>\n")
            f.write(f"<li>{numUnitsInsideUnits} units completely contained inside another</li>\n")
            f.write(f"<li>Average number of neighbors: {avgNbrs}</li>\n")
            f.write(f"<li>Highest degree of connectivity: {maxNbrs}</li>\n")
            f.write(f"<li>Average, maximum, and minimum Polsby-Popper scores: {avgPolsPop}, {maxPolsPop}, {minPolsPop}</li>\n")
            f.write( "</ul>\n\n")

            if electionDicts is not None:
                f.write(f"<h2 width:100%> Elections Data:</h2>\n")
                picsName = f"{outputName.split('.')[0]}_images/"
                if not os.path.isdir(picsName):
                    os.mkdir(picsName)

                for election in electionDicts.keys():
                    f.write("<p width=100%>\n")
                    electionPlot1 = picsName + election + 'D' + '.png'
                    electionPlot2 = picsName + election + 'R' + '.png'
                    c1 = electionDicts[election]
                    dataFrame[1].plot(column=c1['D'], cmap="Blues")
                    plt.savefig(electionPlot1)
                    dataFrame[1].plot(column=c1['R'], cmap="Reds")
                    plt.savefig(electionPlot2)

                    f.write(f"<h3 width=100%> {election}</h3>\n")
                    f.write(f"    <p width=100%>\nDemocrat totals: {dataFrame[1][electionDicts[election]['D']].sum()}, ")
                    f.write(f"Republican Totals: {dataFrame[1][electionDicts[election]['R']].sum()}\n</p>\n")
                    f.write( '    <div width=100%>\n')
                    f.write(f"        <img src='{electionPlot1}' width=45%/>\n")
                    f.write(f"        <img src='{electionPlot2}' width=45%/>\n")
                    f.write( '    </div>\n')
                    f.write( "</p>\n")

                    f.write("<br>\n")

            if voteColumns is not None:
                f.write(f"<h2 width:100%>Vote Data:</h2>\n")

                f.write(f"<p>\n<table>\n<tr><th>Column Name</th><th>Total Count</th><th>Max</th><th>Min</th><th>Average</th></tr>\n")
                for column in voteColumns:
                    maxCol=max(dataFrame[1][column])
                    minCol=min(dataFrame[1][column])
                    avgCol=np.mean(dataFrame[1][column].tolist())
                    f.write("<tr>\n")
                    f.write(f"<td>{column}</td>\n")
                    f.write(f"<td>{dataFrame[1][column].sum()}</td>\n")
                    f.write(f"<td>{maxCol}</td>\n")
                    f.write(f"<td>{minCol}</td>\n")
                    f.write(f"<td>{avgCol}</td>\n")
                    f.write("</tr>\n")
                f.write("</table>\n</p>\n")
                f.write("<br>\n")

            f.write("</body>\n")
            f.write("</html>\n")

    elif shapefileName is not None:
        sname = os.path.basename(shapefile.split('.shp')[0])
        dataFrame = [sname, gp.read_file(shapefileName)]
        generic_shapefile_report(outputName, dataFrame, idColumn=idColumn, voteColumns=voteColumns, electionDicts=electionDicts)



def prorate_report(
        reportOutputFileName="ProrateReport.html",
        bigDF=None,
        basicDF=None,
        smallDF=None,
        big_geoid=None,
        basic_geoid=None,
        small_geoid=None,
        population=None,
        voteColumns=None,
        electionDicts=None):

        with open(reportOutputFileName, "w") as f:
            f.write("<html>\n")
            write_header_styles(f)

            bigAvgArea = np.mean([x.area for x in bigDF[1]['geometry']])
            bigAvgPOP = np.mean([x.area/ (x.length**2) for x in bigDF[1]['geometry']])
            basicAvgArea = np.mean([x.area for x in basicDF[1]['geometry']])
            basicAvgPOP = np.mean([x.area/ (x.length**2) for x in basicDF[1]['geometry']])

            f.write( "<body>\n")
            f.write(f"<h1 width:100%> Proration:</h1>\n")
            f.write(f"<p>{bigDF[0]} written in {basicDF[0]} Units</p>\n")
            f.write( '<div width=100%>\n')
            f.write( '   <div width=45%>\n')
            f.write(f"      {bigDF[0]}:\n")
            f.write( "      <ul>\n")
            f.write(f"          <li> {len(bigDF[0])} geographic units</li>\n")
            f.write(f"          <li> {bigAvgArea} average area per unit</li>\n")
            f.write(f"          <li> {bigAvgPOP} average Polsby-Popper per unit</li>\n")
            f.write( "      </ul>\n")
            f.write( "   </div>\n")
            f.write( '   <div width=45%>\n')
            f.write(f"    {basicDF[0]}:\n")
            f.write(f"    <li> {len(basicDF[0])} geographic units</li>\n")
            f.write(f"    <li> {basicAvgArea} average area per unit</li>\n")
            f.write(f"    <li> {basicAvgPOP} average Polsby-Popper per unit</li>\n")
            f.write( "  </div>\n")
            f.write("</div>\n")

            if electionDicts is not None:
                f.write(f"<h2 width:100%> Elections Data:</h2>\n")
                picsName = f"{outputName.split('.')[0]}_images/"
                if not os.path.isdir(picsName):
                    os.mkdir(picsName)

                f.write(f"<table>\n<tr><th></th><th>{dataDFName}</th><th>{chainDFName}</th></tr>\n")
                for election in electionDicts.keys():
                    f.write(f"<h3 width=100%> {election}</h3>\n")
                    f.write("<tr>")
                    f.write(f"<td> Republican Totals </td>\n")
                    f.write("<td>" + str(bigDF[1][electionDicts[election]['R']].sum()) + "</td>\n")
                    f.write("<td>" + str(basicDF[1][electionDicts[election]['R']].sum()) + "</td>\n")
                    f.write("</tr>\n")
                    f.write("<tr>\n")
                    f.write(f"<td> Democrat Totals </td>")
                    f.write("<td>" + str(bigDF[1][electionDicts[election]['D']].sum()) + "</td>\n")
                    f.write("<td>" + str(basicDF[1][electionDicts[election]['D']].sum()) + "</td>\n")
                    f.write("</tr>\n")
                f.write("</table>\n")

                for election in electionDicts.keys():
                    electionPlot1 =  picsName + election + 'D' + '.png'
                    electionPlot2 =  picsName + election + 'R' + '.png'
                    delectionPlot1 = picsName + 'orig_' + election + 'D' + '.png'
                    delectionPlot2 = picsName + 'orig_' + election + 'R' + '.png'

                    basicDF[1].plot(column=electionDicts[election]['D'], cmap='Blues')
                    plt.title(f"prorated to {basicDFName}")
                    plt.savefig(electionPlot1)
                    plt.clf()
                    bigDF[1].plot(column=electionDicts[election]['D'], cmap='Blues')
                    plt.title(f"original data source: {bigDFName}")
                    plt.savefig(delectionPlot1)
                    plt.clf()
                    basicDF[1].plot(column=electionDicts[election]['R'], cmap='Reds')
                    plt.title(f"prorated to {basicDFName}")
                    plt.savefig(electionPlot2)
                    plt.clf()
                    bigDF[1].plot(column=electionDicts[election]['R'], cmap='Reds')
                    plt.title(f"original data source: {bigDFName}")
                    plt.savefig(delectionPlot2)
                    plt.clf()

                    f.write(f"<h1 width:100%>{election} Election:</h1>\n")
                    f.write('<div width=100%>\n')
                    f.write(f"   <img src='{delectionPlot1}' width=45%/>\n")
                    f.write(f"   <img src='{electionPlot1}'  width=45%/>\n")
                    f.write( '</div>\n')
                    f.write('<div width=100%>\n')
                    f.write(f"   <img src='{delectionPlot2}' width=45%/>\n")
                    f.write(f"   <img src='{electionPlot2}'  width=45%/>\n")
                    f.write('</div>\n')

            if voteColumns is not None:
                f.write(f"<h2 width=100%> Voting Data:</h2>\n")
                """
                picsName = f"{outputName.split('.')[0]}_images/"
                if not os.path.isdir(picsName):
                    os.mkdir(picsName)
                """
                f.write(f"<h3 width=100%> Original counts</h3>\n")
                f.write(f"<p>\n<table>\n<tr><th>Column Name</th><th>Total Count</th><th>Max</th><th>Min</th><th>Average</th></tr>\n")
                for column in voteColumns:
                    maxCol=max(bigDF[1][column])
                    minCol=min(bigDF[1][column])
                    avgCol=np.mean(basicDF[1][column].tolist())
                    f.write("<tr>\n")
                    f.write(f"<td>{column}</td>\n")
                    f.write(f"<td>{bigDF[1][column].sum()}</td>\n")
                    f.write(f"<td>{maxCol}</td>\n")
                    f.write(f"<td>{minCol}</td>\n")
                    f.write(f"<td>{avgCol}</td>\n")
                    f.write("</tr>\n")
                f.write("</table>\n</p>\n")

                f.write(f"<h3 width=100%> Prorated counts</h3>\n")
                f.write(f"<p>\n<table>\n<tr><th>Column Name</th><th>Total Count</th><th>Max</th><th>Min</th><th>Average</th></tr>\n")
                for column in voteColumns:
                    maxCol=max(basicDF[1][column])
                    minCol=min(basicDF[1][column])
                    avgCol=np.mean(basicDF[1][column].tolist())
                    f.write("<tr>\n")
                    f.write(f"<td>{column}</td>\n")
                    f.write(f"<td>{basicDF[1][column].sum()}</td>\n")
                    f.write(f"<td>{maxCol}</td>\n")
                    f.write(f"<td>{minCol}</td>\n")
                    f.write(f"<td>{avgCol}</td>\n")
                    f.write("</tr>\n")
                f.write("</table>\n</p>\n")
                f.write("<br>\n")



            f.write("</body>\n")
            f.write("</html>\n")


def roundoff_report(
        reportOutputFileName="RoundoffReport.html",
        bigDF=None,
        basicDF=None,
        big_geoid=None,
        basic_geoid=None):

        with open(reportOutputFileName, "w") as f:

            picsName = f"{reportOutputFileName.split('.')[0]}_images/"
            if not os.path.isdir(picsName):
                os.mkdir(picsName)

            bigUnits = picsName+"bigV.png"
            basicUnits = picsName+"basicV.png"
            roundedUnits = picsName+"roundedV.png"

            bigDF.plot(column=big_geoid)
            plt.title("Before Rounding")
            plt.savefig(bigUnits)

            basicDF.plot(column=basic_geoid)
            plt.title("Roundoff Units")
            plt.savefig(basicUnits)

            basicDF.plot(column='CD')
            plt.title("After Rounding")
            plt.savefig(roundedUnits)

            f.write("<html>\n")
            write_header_styles(f)
            f.write("<body>\n")

            f.write(f"<h3 width=100%> Roundoff Results</h3>\n")
            f.write( "<p>\n")
            f.write( '    <div width=100%>\n')
            f.write(f"        <img src='{bigUnits}' width=30%/>\n")
            f.write(f"        <img src='{basicUnits}' width=30%/>\n")
            f.write(f"        <img src='{roundedUnits}' width=30%/>\n")
            f.write( '    </div>\n')
            f.write( "</p>\n")

            f.write("</body>\n")
            f.write("</html>\n")


