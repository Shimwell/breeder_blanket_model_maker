
from HCLL_CAD_procedure import *
from DCLL_CAD_procedure import *
from WCLL_CAD_procedure import *
from HCPB_CAD_procedure import *

def detailed_module(blanket_geometry_parameters):

    if blanket_geometry_parameters['blanket_type'].upper() == 'HCLL' :
       HCLL_detailed_module(blanket_geometry_parameters) 

    elif blanket_geometry_parameters['blanket_type'].upper() == 'DCLL' :
       DCLL_detailed_module(blanket_geometry_parameters) 

    elif blanket_geometry_parameters['blanket_type'].upper() == 'WCLL' :
       WCLL_detailed_module(blanket_geometry_parameters) 

    elif blanket_geometry_parameters['blanket_type'].upper() == 'HCPB' :
       HCPB_detailed_module(blanket_geometry_parameters)               

    else:
        print('Blanket type ',blanket_geometry_parameters['blanket_type'],' not supported yet.')