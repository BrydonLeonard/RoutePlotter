import gpxpy
import gpxpy.gpx
import math
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
import os
import subprocess
import logging
import random
import shutil

logging.basicConfig(level=logging.INFO)

R = 6371

COLOR1 = "#22FFFF"
COLOR2 = "#222222"

def padLeft(hexString):
    return "".join(str(x) for x in ([0] * (2 - hexString.length))) + hexString

def randomColor(dim, otherColor = 0):
    h = 220
    while (h > 205 and h < 275):
        h = random.randrange(360)

    s = 255
    b = 255

    if (dim):
        b = b - 180
        s = s - 100
        h = (otherColor + random.randrange(20) - 10) % 360

    return "hsb(%s,%s,%s)" % (h,s,b), h

#Process a folder of gpx files into images
def processFolder(folder):
    files = os.listdir(folder)

    logging.info("Removing old files")
    if (os.path.isdir("./working")):
        shutil.rmtree("working")
    os.mkdir("working")

    if (os.path.isdir("output")):
        shutil.rmtree("output")
    os.mkdir("output")

    logging.info("Old files cleared")

    for file in files:
        logging.info("Processing route " + file)
        gpx_file = open(folder + "/" + file, 'r')
        gpx = gpxpy.parse(gpx_file)

        #Slightly lazy, but just removes ".gpx"
        filename = file[:-4]

        logging.info("  Parsing route")
        path = processGpx(gpx)

        logging.info("  Clearing old plots")
        plt.clf()
        plt.cla()
        plt.close()

        logging.info("  Plotting route")
        fig = getPrettyPathFig(path)

        logging.info("  Saving plot")
        plotFileName = "working/" + filename + "_plot.png"
        fig.savefig(plotFileName, bbox_inches='tight', pad_inches=0, facecolor="#151515", dpi=300)

        logging.info("  Creating gradient")
        gradFileName = "working/" + filename + "_grad.png"
        (col1, h1) = randomColor(False)
        (col2, _) = randomColor(True, h1)
        subprocess.run("magick -size 1300x1300 radial-gradient:" + col1 + "-" + col2 + "  -extent 1115x1115+92.5+92.5 " + gradFileName)

        logging.info("  Combining plot and gradient")
        finalFileName = "output/" + filename + "_final.png"
        logging.info("  Combining gradient and plot")
        subprocess.run("magick convert " + plotFileName + " " + gradFileName + " -compose Multiply -composite " + finalFileName)

        logging.info("  Completed " + filename)

    logging.info("Creating montage")
    subprocess.run("magick montage ./output/*.png -geometry 800x800 -frame 2 ./montage.png")

    logging.info("Done")


#Convert a path to a plotted image
def getPrettyPathFig(path):
    patch = patches.PathPatch(path, facecolor=None, lw=2.5, fill=False, edgecolor="#DDDDDD")
    fig = plt.figure(frameon=False)

    ax = fig.add_subplot(111)
    ax.add_patch(patch)
    ax.autoscale(enable=True, axis='both', tight=False)
    ax.get_yaxis().set_visible(False)
    ax.get_xaxis().set_visible(False)
    ax.set_axis_off()
    ax.set_aspect('equal')

    #Equalise axis sizes
    xLim = ax.get_xlim()
    yLim = ax.get_ylim()
    xSize = xLim[1] - xLim[0]
    ySize = yLim[1] - yLim[0]

    if (xSize > ySize):
        yMid = (yLim[1] + yLim[0]) / 2
        newScale = xSize / 2
        yNewLim = [yMid - newScale, yMid + newScale]
        ax.set_ylim(yNewLim)
    else:
        xMid = (xLim[1] + xLim[0]) / 2
        newScale = ySize / 2
        xNewLim = [xMid - newScale, xMid + newScale]
        ax.set_xlim(xNewLim)
    ax.set_aspect('equal')

    return fig

#Process a gpx file into a matplotlib path
def processGpx(gpx):
    cartPoints = []
    pltLineCodes = []

    for track in gpx.tracks:
        startPoint = None
        for segment in track.segments:
            for point in segment.points:
                #For small distances, lon-lat can map directly to x-y
                xCart = point.longitude
                yCart = point.latitude

                #Center the route
                if (startPoint == None):
                    startPoint = [xCart, yCart]
                    pltLineCodes.append(Path.MOVETO)
                    cartPoints.append([0,0])
                else:
                    cartPoints.append((xCart - startPoint[0], yCart - startPoint[1]))
                    pltLineCodes.append(Path.LINETO)
    return Path(cartPoints, pltLineCodes)


processFolder('gpxData')
