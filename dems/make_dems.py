#!/usr/bin/env python

import sys
sys.path.insert(0,'../scripts')
import argparse

import os
from geodat import *
from geotif import *

import postprocess_jak

velocity_data = {
    'helheim': 'TSX_E66.50N_27Jan09_07Feb09',
    'kangerd': 'TSX_E68.80N_28Jan09_08Feb09',
    'jakobshavn': 'mosaicOffsets'
}


# ---------------------------------------------------------------------------- #
def main(argv):                                                                #
# ---------------------------------------------------------------------------- #
    # Parse command line arguments
    dem_source = "morlighem"

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dem", required = True,
                        help = "DEM source, either 'cresis' or 'morlighem'")
    args, _ = parser.parse_known_args(argv)
    dem_source = args.dem

    if not dem_source in ("morlighem", "cresis"):
        print("Unrecognized DEM source " + dem_source + ", should be\n"
              "either \"cresis\" or \"morlighem\"\n")
        sys.exit(1)

    # Make velocity data files
    for glacier in velocity_data.keys():
        if not os.path.exists(glacier):
            os.makedirs(glacier)

        # Check to see if the velocity data have already been made
        if not( os.path.exists(glacier + '/UDEM.xy') or
                os.path.exists(glacier + '/VDEM.xy') or
                os.path.exists(glacier + '/EUDEM.xy') or
                os.path.exists(glacier + '/EVDEM.xy')):

            # Read in the raw velocity data files
            filename = '../data/' + glacier + '/' + velocity_data[glacier]
            x, y, vx = read_geodat(filename + ".vx")
            _, _, vy = read_geodat(filename + ".vy")
            _, _, ex = read_geodat(filename + ".ex")
            _, _, ey = read_geodat(filename + ".ey")

            # Find the points where there actually is measured velocity data
            (I, J) = np.where(vx != -2.0e+9)
            (imin, imax) = (min(I)-2, max(I)+2)
            (jmin, jmax) = (min(J)-2, max(J)+2)
            del I, J

            vx = vx[imin: imax+1, jmin: jmax+1]
            vy = vy[imin: imax+1, jmin: jmax+1]
            ex = ex[imin: imax+1, jmin: jmax+1]
            ey = ey[imin: imax+1, jmin: jmax+1]

            x = x[jmin: jmax+1]
            y = y[imin: imax+1]
            nx = jmax - jmin + 1
            ny = imax - imin + 1

            # Write out the velocity data
            fidu = open(glacier + '/UDEM.xy', 'w')
            fidv = open(glacier + '/VDEM.xy', 'w')
            fideu = open(glacier + '/EUDEM.xy', 'w')
            fidev = open(glacier + '/EVDEM.xy', 'w')

            for fid in [fidu, fidv, fideu, fidev]:
                fid.write('{0}\n{1}\n'.format(nx, ny))

            for j in range(nx):
                for i in range(ny):
                    fidu.write('{0} {1} {2}\n'.format(x[j], y[i], vx[i,j]))
                    fidv.write('{0} {1} {2}\n'.format(x[j], y[i], vy[i,j]))
                    fideu.write('{0} {1} {2}\n'.format(x[j], y[i], ex[i,j]))
                    fidev.write('{0} {1} {2}\n'.format(x[j], y[i], ey[i,j]))

            for fid in [fidu, fidv, fideu, fidev]:
                fid.close()

            # Delete the velocities
            del vx, vy, ex, ey

        print("Done making velocity data for " + glacier)


    # ----------------------------------
    # Make surface / bed elevation data
    # ----------------------------------

    url = "http://students.washington.edu/shapero/"

    # Retrieve bed DEMs from my website
    bed_dem_url = url + "bed_dems/" + dem_source + "/"
    for glacier in ["helheim", "kangerd", "jakobshavn"]:
        # Check whether or not the be DEM has already been made
        if not os.path.exists(glacier + "/zbDEM.xy"):
            os.system("wget " + bed_dem_url
                        + glacier + "/zbDEM.xy -P " + glacier)

        print ("Done making bed elevation data for " + glacier)


    # Retrieve GIMP surface DEMs for Helheim & Kangerd from my website
    surface_dem_url = url + "surface_dems/"
    for glacier in ["helheim", "kangerd"]:
        if not os.path.exists(glacier + "/zsDEM.xy"):
            os.system("wget " + surface_dem_url
                         + glacier + "/zsDEM.xy -P " + glacier)

        print ("Done making surface elevation for " + glacier)


    # Make DEMs for Jakobshavn from special data
    if not os.path.exists("jakobshavn/zsDEM.xy"):
        # read the raw data
        x, y, s = read_geodat("../data/jakobshavn/dem13Mar.smooth")
        nx = len(x)
        ny = len(y)

        # write out the surface data in the format Elmer expects
        fid = open("jakobshavn/zsDEM.xy", "w")
        fid.write("{0}\n{1}\n".format(nx, ny))
        for j in range(nx):
            for i in range(ny):
                fid.write('{0} {1} {2}\n'.format(x[j], y[i], s[i, j]))
        fid.close()

    print ("Done making surface elevation for Jakobshavn")

    # Post-process the Jakobshavn velocities to interpolate over some small
    # gaps in the observational data
    postprocess_jak.main()

    print("Done post-processing Jakobshavn velocity data")


if __name__ == "__main__":
    main(sys.argv[1:])

