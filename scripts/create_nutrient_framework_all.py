# Script to generate unifhy-compliant ancillary files from
# those on the EIDC at:
# https://catalogue.ceh.ac.uk/documents/6da95899-f3b8-4089-b621-560818aa78ba
#
# Specifically, a unifhy-compliant version of the flow-direction
# and catchment area files are produced, as well as a unifhy-compliant
# land-sea mask derived from the catchment area file. 
# MJB, UKCEH, 18/10/22

import cf
import os
import sys
import glob
import numpy
import unifhy
from datetime import datetime, timedelta

######################################################################
# User config
######################################################################

# directory containing EIDC files
indir = '/home/users/mattjbr/unifhy/unifhy_driving_files/ancillary'

# directory to output unifhy-compliant files
outdir = '/home/users/mattjbr/unifhy/unifhy_driving_files/ancillary/framework_compliant'

# these shouldn't need to be changed if using the files 
# straight from the EIDC but they are, in order,
# the main part of the filename, then the variable name
# within each corresponding file, and then the corresponding
# standard name, or as close to one as we can get. 
file_names = ["uk_catchment_areas_1km", 
              "UK_outflow_drainage_directions_1km_test"]
var_names = {"uk_catchment_areas_1km": "catchment_area",
             "UK_outflow_drainage_directions_1km_test": "outflow drainage_directions"}
std_names = {'uk_catchment_areas_1km': 'catchment_area',
             'UK_outflow_drainage_directions_1km_test': 'flow direction'}

# catchment area filename, also shouldn't need to be changed
catareafile = 'uk_catchment_areas_1km.nc'

######################################################################
# Main code
######################################################################

# create output dir
if not os.path.exists(outdir):
    os.makedirs(outdir)

# create spatial domain encompassing whole UK, as an OSGB grid
# Note that this does chop off the eastern most part of the files 
# as unifhy does not currently support OSGB grids with x-coordinates
# below zero. 
bng = unifhy.BritishNationalGrid.from_extent_and_resolution(
    projection_y_coordinate_extent=(0, 1057E3),
    projection_x_coordinate_extent=(0, 656E3),
    projection_y_coordinate_resolution=1000,
    projection_x_coordinate_resolution=1000).to_field()

# Create flow direction and catchment area files
for file_name in file_names:
    # input filename
    fn = glob.glob(os.path.join(indir, file_name + "*.nc"))[0]
    print('Reading from ' + fn)
    
    # read in input data
    field = cf.read(fn)
    
    # Create new netcdf 'field' (variable), copying the grid field
    fld = bng.copy()
    
    # copy the data from the input file into the field
    fld.set_data(field[0][163:,:][::-1,:].data, axes=('Y', 'X'))
    
    # set missing value to -9999 as in original file
    fld._FillValue = -9999
    
    # set the attributes and names
    fld.long_name = std_names[file_name]
    fld = fld.override_units("1")
    fld.nc_set_variable(var_names[file_name])
    
    # write to new file
    ofile = os.path.join(outdir, os.path.basename(fn))
    print('Outputting to ' + ofile)
    cf.write(fld, ofile, compress=4) 
    
# Create land-sea mask
lsmoutfile1 = os.path.join(outdir, 'uk_lsm_derived_from_catchment_areas_1km_temp.nc')
lsmoutfile2 = os.path.join(outdir, 'uk_lsm_derived_from_catchment_areas_1km.nc')
var_name = "landfrac"
std_name = 'land_binary_mask'

# create land-sea mask from the catchment area file, copying the
# method RFM uses
catareafile = os.path.join(indir, catareafile)
ofacc = xr.load_dataset(catareafile)['catchment_area']
ofacc = xr.where(np.isnan(ofacc), -9999, ofacc)
sea = np.where(ofacc < 0)
land = np.where((ofacc < 1) & (ofacc >= 0))
riv = np.where(ofacc >= 1)
rfmmask = np.ones(ofacc.shape)
rfmmask[sea] = 0
ofacc.values = rfmmask
ofacc = ofacc.rename('landfrac')
ofacc.to_netcdf(lsmoutfile1)

# input filename
fn = lsmoutfile1
print('Reading from ' + fn)

# read in input data
field = cf.read(fn)

# Create new netcdf 'field' (variable), copying the grid field
fld = bng.copy()

# copy the data from the input file into the field
fld.set_data(field[0][163:,:][::-1,:].data, axes=('Y', 'X'))

# set the attributes and names
fld.long_name = std_name
fld = fld.override_units("1")
fld.nc_set_variable(var_name)

# write to new file
print('Outputting to ' + lsmoutfile2)
cf.write(fld, lsmoutfile2, compress=4) 



