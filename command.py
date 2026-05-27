from uplc_conf import generate_all_methods 
from uplc_conf import generate_csv_conf

generate_all_methods(
    isocratic_time=4.0,
    gradient_time=6.0,
    initial_org=20.0)

generate_csv_conf(file_name = "test_conf", sample_location = "2:48", conf_names ="iteration_16",  output_dir = "./")