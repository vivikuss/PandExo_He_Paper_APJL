import warnings
import pandexo.engine.justdoit as jdi
import pandexo.engine.justplotit as jpi
import numpy as np
import patch_numpy
import os
import pickle
import matplotlib.pyplot as plt

### ADJUST THIS PART ###
# Paths
#os.environ['pandeia_refdata'] = '/Users/new/Dropbox/APJL_paper_26/THESIS_PandExo-master/pandeia_data-4.1-jwst' 
os.environ['PYSYN_CDBS'] = '/Users/new/Dropbox/APJL_paper_26/THESIS_PandExo-master/grp/redcat/trds' 
os.environ['EXOCTK_DATA'] = '/Users/new/Dropbox/APJL_paper_26/THESIS_PandExo-master/path/to/venv/lib/python3.12/site-packages/exoctk/data'
pic = '/Users/new/Desktop/Thesis_picaso-master-main'
# input_paths = [pic + '/spectrum_k218b_case1',pic + '/spectrum_k218b_case2', pic + '/spectrum_k218b_case3']  
# output_paths = ['pandexo_k218b_spectrum1.txt','pandexo_k218b_spectrum2.txt','pandexo_k218b_spectrum3.txt']
input_paths = [pic + '/spectrum_lhs_case_new1',pic + '/spectrum_lhs_case_new2', pic + '/spectrum_lhs_case_new3']  
output_paths = ['pandexo_lhs_spectrum_new1.txt','pandexo_lhs_spectrum_new2.txt','pandexo_lhs_spectrum_new3.txt']
####
### also set all three using: export pandeia_refdata="path", echo 'export pandeia_refdata="path"' >>~/.bash_profile
### check using: python -c "import pandeia.engine; pandeia.engine.pandeia_version()"
###

# double check path
print("pandeia refdata:", os.environ.get("pandeia_refdata"))

### CUSTOMIZE IF NEEDED ###
### K2-18b ###
# # Planet's Properties
# mpla = 0.0272           # Mjup ##### Benneke 2019
# rpla = 0.2328           # Rjup ##### Benneke 2019
# ps = 20

# # Star's Properties
# tstel = 3500            # K               
# met = 0.123             # dex          
# g = 4.858               # log g value       
# rstel = 0.4445            # Rsun             
# mag = 8.899

### LHS 1140b ###
# Planet's Properties ##### Data from Damiano et al. (2024)
mpla = 0.0176           # Mjup 
rpla = 0.1543            # Rjup 
ps = 20

# Star's Properties
tstel = 3500             # K               
met = -0.15            # dex          
g = 5.0               # log g value       
rstel = 0.2159              # Rsun             
mag = 9.612                            

####################################################

# observation settings
exo_dict = jdi.load_exo_dict()
exo_dict['observation']['sat_level'] = 80         # saturation level in percent of full well 
exo_dict['observation']['sat_unit'] = '%' 
exo_dict['observation']['noccultations'] = 2        #number of transits 
exo_dict['observation']['R'] = None                   # no binning
exo_dict['observation']['baseline'] = 0.35          # fraction of time in transit versus out 
exo_dict['observation']['baseline_unit'] = 'frac' 
exo_dict['observation']['noise_floor'] = 0              

# star properties
exo_dict['star']['type'] = 'phoenix'                # phoenix or user
exo_dict['star']['mag'] = mag                      # star's magnitude 
exo_dict['star']['ref_wave'] = 1.25               # for J mag = 1.25, H = 1.6, K =2.22.. etc (all in micron)
exo_dict['star']['temp'] = tstel                   # K 
exo_dict['star']['metal'] = met                   # log Fe/H
exo_dict['star']['logg'] = g                        # log g
exo_dict['star']['radius'] = rstel                   # stellar radius
exo_dict['star']['r_unit'] = 'R_sun'   

# planet properties
exo_dict['planet']['type'] = 'user'
exo_dict['planet']['mass'] = mpla
exo_dict['planet']['m_unit'] = 'M_jup' 
exo_dict['planet']['radius'] = rpla                      # other options include "um","nm" ,"Angs", "secs" (for phase curves)
exo_dict['planet']['r_unit'] = 'R_jup'  
exo_dict['planet']['w_unit'] = 'um' 
exo_dict['planet']['transit_duration'] = 2.0*60.0*60.0 
exo_dict['planet']['td_unit'] = 's'
exo_dict['planet']['f_unit'] = 'rp^2/r*^2'

# instrument settings
inst_dict = jdi.load_mode_dict('NIRSpec PRISM')       # using NIRSpec PRISM

# print(inst_dict["configuration"].keys())
# print("detector keys:", inst_dict["configuration"]["detector"].keys())
# print("instrument:", inst_dict["configuration"]["instrument"])
# print("detector:", inst_dict["configuration"]["detector"])
# exit()
# inst_dict["configuration"]["detector"]["readout_pattern"] = "nrsrapid"
# inst_dict["configuration"]["detector"]["readmode"] = "nrsrapid"
# inst_dict["configuration"]["detector"]["subarray"] = "sub512"
inst_dict["configuration"]["detector"]["ngroup"] = 2    #running "optimize" will select the max, possible groups before sat, integer between 2-65536
inst_dict["configuration"]["detector"]["nint"] = 2000
inst_dict['background'] = 'ecliptic'                            # options: ecliptic or minzodi
inst_dict['background_level'] = 'medium'                       # options: low, medium, high

for k,(in_path, out_path) in enumerate(zip(input_paths,output_paths)):
    print('Starting run ', k) 

    # generate spectra
    exo_dict['planet']['exopath'] = in_path + '.txt'

    # import json, copy
    # tmp = copy.deepcopy(inst_dict)
    # # pandexo wraps pandeia input; depending on your code, inst_dict might already be the "pandeia_input"
    # print("instrument:", tmp.get("instrument", tmp.get("configuration",{}).get("instrument")))
    # print("mode:", tmp.get("mode", tmp.get("configuration",{}).get("mode")))
    # print("exposure keys:", tmp.get("exposure", tmp.get("configuration",{}).get("exposure", {})))
    # print("subarray keys:", tmp.get("subarray", tmp.get("configuration",{}).get("subarray", {})))


    results = jdi.run_pandexo(exo_dict, inst_dict, save_file=True)
    filename = 'pandexo_results_'+str(out_path)+'_'+str(exo_dict['observation']['noccultations'])+'transits_'
    print("Generating Output File")
    outfile = open(filename, 'wb')
    pickle.dump(results, outfile)
    outfile.close()

    with open(filename, 'rb') as infile:
        results = pickle.load(infile)

    # check for warnings
    print("Warnings:", results["warning"])  

    # debugging
    signal = results["RawData"]["electrons_out"]
    noise = results["RawData"]["error_no_floor"]
    sn_estimate = signal / noise

    # save to txt file as well
    final_spectrum = results["FinalSpectrum"] 

    # extract the wavelength and transit depth
    wavelengths = final_spectrum["wave"]                        # wavelengths in um
    transit_depth = final_spectrum["spectrum"]                 # transit depth in Rp^2/R*^2
    sim_transit = final_spectrum["spectrum_w_rand"]          # includes noise
    error_bars = final_spectrum["error_w_floor"]              # uncertainty values

    # stack into array
    data_to_save = np.column_stack((wavelengths, transit_depth, sim_transit, error_bars))

    # save to a text file
    np.savetxt(out_path, data_to_save, fmt="%.6f", header="Wavelength (µm) Transit Depth (Rp^2/Rs^2)", comments='')
