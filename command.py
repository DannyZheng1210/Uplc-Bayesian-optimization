from uplc_conf import generate_all_methods 
from uplc_conf import generate_csv_conf
from read_data import read_chromatogram

"""
variables here
"""
iso_time = 1.0
gradient_time = 1.0
initial_org = 20.0
'''
configuration file parameters here
'''
conf_files_name = "test_2"
configuration_files_folder = "./"
csv_control_file_folder = "./"
sample_location = "2:48"

generate_all_methods(
    isocratic_time=iso_time,
    gradient_time=gradient_time,
    initial_org=initial_org,
    output_dir = configuration_files_folder,
    conf_files_name = conf_files_name)


generate_csv_conf(file_name = conf_files_name, sample_location = sample_location, conf_names = conf_files_name, output_dir = csv_control_file_folder)

"""
read data from chromatogram code here
"""
# read_chromatogram(chromatogram_rawdata, chromatogram_csv="./")

#define the chromatogram rawdata file and the output folder address for the csv file


'''
analysis chromatogram data here
'''



'''
Bayesian optimization code here
'''



"""
close loop control code here
"""

