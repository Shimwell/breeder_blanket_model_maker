import sys, re, os
from neutronics_material_maker import *
from collections import Counter
import collections
from collections import OrderedDict


def return_serpent_file_head(include_um_mesh):
    lines_for_file=[]
    lines_for_file.append('% run this file using one of the following three commands')
    lines_for_file.append('%     sss2 filename -tracks 100 ')
    lines_for_file.append('%     sss2 filename -omp 2 ')
    lines_for_file.append('%     sss2 filename')
    lines_for_file.append(' ')
    lines_for_file.append(' ')
    lines_for_file.append('% model stl files')
    lines_for_file.append('surf 999  sph 0 0 0 4000 %base units are cm')
    lines_for_file.append('surf 998  sph 0 0 0 4001')
    lines_for_file.append('\n\n% CSG cells')
    lines_for_file.append('cell 1000  0 fill sector -999 %sphere fill with universe sector')
    #lines_for_file.append('cell 1999  0 outside 999')
    lines_for_file.append('cell 1999  0 outside 999 ')# -998')

    if include_um_mesh==True:
        lines_for_file.append('cell 10    0 fill=all_um_geometry   -999 ')

    lines_for_file.append('\n\n%background universe cell = void')
    lines_for_file.append('cell 2000  bg_for_stl void -998 % background universe number 2')
    lines_for_file.append('\n\n')

    if include_um_mesh==True:

        lines_for_file.append('solid 1 all_um_geometry bg_for_stl')
        lines_for_file.append('1000 2 10 5   % search mesh parameters for octree')
        lines_for_file.append('points')
        lines_for_file.append('faces')
        lines_for_file.append('owner')
        lines_for_file.append('neighbour')
        lines_for_file.append('matfile')

    lines_for_file.append('\n\n% ------  stl cells in universe 1 ------\n% background is universe 2 which is just void')
    lines_for_file.append('solid 2  sector bg_for_stl   %solid 2 is stl.  <uni> <bg uni>')
    lines_for_file.append('100 3 10 5 5     %adaptive search mesh parameters')
    lines_for_file.append('%<max cells under mesh before split> <n levels> <size 1> < size 2> < size n>')
    lines_for_file.append('% here initial search mesh is 10x10x10, any mesh with > 5 cells under it is split into a 5x5x5 mesh.')
    lines_for_file.append('1 0.0000001   %1=fast, 2=safe tracking mode.  verticies snap tolerence.')
    lines_for_file.append('% these made no difference to error\n\n')

    return lines_for_file

def return_serpent_file_stl_parts(components,material_dictionary,output_folder_stl,output_folder):


    print(output_folder_stl)
    print(output_folder)
    print(os.path.commonprefix([output_folder_stl,output_folder]))

    relative_dir= output_folder_stl[len(os.path.commonprefix([output_folder_stl, output_folder])):].lstrip('/')

    print('relative director for stl files ' ,relative_dir)

    lines_for_file = []
    #number_of_stl_parts=0
    for component in components:
        # print(component)
        # if component['stl']==True:
        print('body ' + component + '-b ' + component + '-c ')
        lines_for_file.append('body ' + component + '-b ' + component + '-c ' + material_dictionary[component].material_card_name)
        for part in components[component]:
            stl_filepaths = part['stl_filename']
            for stl_filepath in stl_filepaths:
                stl_filename = os.path.split(stl_filepath)[-1]
                stl_filename_base = os.path.splitext(stl_filename)[0]
                # print('stl_filepath',stl_filepath)
                # print('stl_filename',stl_filename)
                # print('stl_filename_base',stl_filename_base)


                relative_filepath = os.path.join(relative_dir, stl_filename)
                lines_for_file.append('    file ' + component + '-b "' + relative_filepath + '" 0.1 0 0 0  ')

            #number_of_stl_parts=number_of_stl_parts+1
        lines_for_file.append('\n\n')

    return lines_for_file#,number_of_stl_parts

def return_serpent_file_run_params(plot_serpent_geometry,tallies,nps):


    lines_for_file=[]
    lines_for_file.append('  ')
    lines_for_file.append('  ')
    lines_for_file.append('% ---- RUN ----')
    lines_for_file.append('set outp 1000')
    lines_for_file.append('set srcrate 1.0')
    lines_for_file.append('set acelib "/opt/serpent2/xsdir.serp"')

    lines_for_file.append('\n\n')

    lines_for_file.append("set gcu -1")
    # # lines_for_file += ["set opti 1"] # can be used to limit memory use

    lines_for_file.append("set lost 100")  # allows for 100 lost particles
    lines_for_file.append("set usym sector 3 2 0.0 0.0 0 10") #a 10 degree slice with boundary conditions

    for tally in tallies:
        particle_type= tally['particle_type']
        if particle_type =='p':
            print('Tally with photons found, including photons in the simulation')
            lines_for_file += ["set ngamma 2 %analog gamma"]
            lines_for_file += ['set pdatadir "/opt/serpent2/photon_data/"']
            lines_for_file += ['set ekn']
            break

    
    batch_size = min(0.5 * nps, 5000)
    # make batch size 1e4 regardless of nps
    batches = int(nps / batch_size)
    print('nps ', nps)
    print('batch_size ', batch_size)
    print('batches ', batches)

    lines_for_file.append('set nps ' + str(nps) + ' ' + str(batches) + ' % neutron population, bunch count')
    lines_for_file.append('set outp ' + str(batches + 1) + ' %only prints output after batchs +1, ie at the end')



    if plot_serpent_geometry == True:

        lines_for_file.append('plot 1 16800 16800 -2  -2100 2100 -2100 2100')
        lines_for_file.append('plot 2 16800 16800 -2  -2100 2100 -2100 2100 %plot py pixels pixels origin')
        lines_for_file.append('plot 3 16800 16800 -2  -2100 2100 -2100 2100')
    lines_for_file.append('\n\n')

    return lines_for_file

def return_serpent_macroscopic_detectors(list_of_bodies_to_tally,mt_number,detector_name,particle_type):#,material_description=''):
  
    lines_list = []
    lines_list.append('\n')
    lines_list.append('% ------------ DETECTOR INPUT (macroscopic) ---------------')
    lines_list.append('det ' + detector_name + ' ' + particle_type)
    for body in list_of_bodies_to_tally:
        lines_list.append("\tdc " + body + "-c")
    lines_list.append('\tdr '+str(mt_number)+' void') # void can be replaced with the material_description but this is not needed

    return lines_list

def return_serpent_file_material_cards(components,material_dictionary):

    #relative_dir = os.path.basename(settings.output_folder_stl)

    lines_for_file = []
    materials_already_added=[]
    for component in components:
        print(component)
        if material_dictionary[component].material_card_name not in materials_already_added:
            lines_for_file.append('\n\n')

            lines_for_file.append(material_dictionary[component].serpent_material_card())
            materials_already_added.append(material_dictionary[component].material_card_name)
        else:
            print('material previous added')
    return lines_for_file

def return_plasma_source(plasma_source_name='EU_baseline_2015') :

    if plasma_source_name == 'EU_baseline_2015':
        idum1 = "1 "
        idum2_number_of_cells_to_follow = "1 "
        idum3_valid_source_cells = "67 " #todo currently hard coded as 67
        rdum1_reactopm_selector = "2.0 " #DT, =1 for DD else is DT
        rdum2_t_in_kev = "10.5 " 
        rdum3_major_rad = "900 "
        rdum4_minor_rad = "225 "
        rdum5_elongation = "1.56 "
        rdum6_triangularity = "0.33 "

        rdum7_plasma_shift = "0.0 " 
        rdum8_plasma_peaking = "1.7 " 
        rdum9_plasma_vertical_shift = "0.0 " 
        rdum10_ang_start = "0 " #todo
        rdum11_ang_extent = "360.0 " #todo


        lines_for_file=[]
        lines_for_file.append('% --------------------- SOURCE SPECIFICATION ---------------------')
        lines_for_file.append('% MUIR GAUSSIAN FUSION ENERGY SPECTRUM IN USER DEFINED SUBROUTINE')
        lines_for_file.append('% PARAMETERS TO DESCRIBE THE PLASMA:')
        lines_for_file.append('src 1 si 16')
        lines_for_file.append('3 11')
        lines_for_file.append(idum1+' % IDUM(1) ')
        lines_for_file.append(idum2_number_of_cells_to_follow+' % IDUM(2) = number of valid cell numbers to follow')
        lines_for_file.append(idum3_valid_source_cells+' % IDUM(3) to IDUM(IDUM(2)+1) = valid source cells')
        lines_for_file.append(rdum1_reactopm_selector+' % RDUM(1) = Reaction selector 1=DD otherwise DT')
        lines_for_file.append(rdum2_t_in_kev+' % RDUM(2) = TEMPERATURE OF PLASMA IN KEV')
        lines_for_file.append(str(float(rdum3_major_rad))+' % RDUM(3) = RM  = MAJOR RADIUS')
        lines_for_file.append(str(float(rdum4_minor_rad))+' % RDUM(4) = AP  = MINOR RADIUS')
        lines_for_file.append(rdum5_elongation+' % RDUM(5) = E   = ELONGATION')
        lines_for_file.append(rdum6_triangularity+' % RDUM(6) = CP  = TRIANGUARITY')
        lines_for_file.append(rdum7_plasma_shift+' % RDUM(7) = ESH = PLASMA SHIFT')
        lines_for_file.append(rdum8_plasma_peaking+' % RDUM(8) = EPK = PLASMA PEAKING')
        lines_for_file.append(rdum9_plasma_vertical_shift+' % RDUM(9) = DELTAZ = PLASMA VERTICAL SHIFT (+=UP)')
        lines_for_file.append(rdum10_ang_start+' % RDUM(10) = Start of angular extent')
        lines_for_file.append(rdum11_ang_extent+'% RDUM(11) = Range of angular extent')
        lines_for_file.append('\n\n')

        return lines_for_file


def find_components(list_of_detailed_modules_components):

    dictionary_of_components=collections.defaultdict(list)
    for item in list_of_detailed_modules_components:
        #print(item)
        for key,value in item.iteritems():
            dictionary_of_components[key].append(value)

    return dictionary_of_components


def make_serpent_stl_based_input_file(neutronics_parameters_dictionary):

    output_folder=neutronics_parameters_dictionary['output_folder']
    components=find_components(neutronics_parameters_dictionary['parts'])
    include_um_mesh=neutronics_parameters_dictionary['include_um_mesh']
    output_folder_stl=neutronics_parameters_dictionary['output_folder_stl']
    material_dictionary=neutronics_parameters_dictionary['material_dictionary']
    #material_description_for_tbr_tally=neutronics_parameters_dictionary['material_description_for_tbr_tally']
    plot_serpent_geometry=neutronics_parameters_dictionary['plot_serpent_geometry']
    tallies=neutronics_parameters_dictionary['tallies']
    nps=neutronics_parameters_dictionary['nps']
    #particle_type=neutronics_parameters_dictionary['particle_type']
        



    serpent_file = []
    serpent_file += return_serpent_file_head(include_um_mesh)
    serpent_file += return_serpent_file_stl_parts(components,material_dictionary,output_folder_stl,output_folder)

    number_of_stl_parts=0
    for line in serpent_file:
        number_of_stl_parts=number_of_stl_parts+line.count('.stl')

    serpent_file += return_serpent_file_run_params(plot_serpent_geometry,tallies,nps)

    serpent_file += return_serpent_file_material_cards(components, material_dictionary)
    
    serpent_file += return_plasma_source()

    for tally in tallies:
        print(tally)
        serpent_file += return_serpent_macroscopic_detectors(list_of_bodies_to_tally=tally['bodies'],
                                                             mt_number=tally['mt_number'],
                                                             detector_name=tally['name'],
                                                             particle_type=tally['particle_type'],
                                                             #material_description=materials[0], void is used 
                                                             )

  

    # if settings.include_um_mesh == 'yes':
    #     serpent_file += 'include "detector"'
    #
    # mesh = False
    # if mesh == True:
    #     serpent_file += return_serpent_file_mesh('li6_mt205')
    #     serpent_file += return_serpent_file_mesh('li7_mt205')
    #     serpent_file += return_serpent_file_mesh('neutron_multiplication')
    directory_path_to_serpent_output = os.path.join(output_folder, 'serpent_input_file.serp')

    with open(directory_path_to_serpent_output, 'w') as serpent_input_file:
        for line in serpent_file:
            serpent_input_file.write(line + '\n')
    print('file written to ',directory_path_to_serpent_output)

    return directory_path_to_serpent_output,number_of_stl_parts




if __name__ == "__main__":

    simulate_the_model_step_by_step()
