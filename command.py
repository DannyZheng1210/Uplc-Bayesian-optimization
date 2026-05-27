from uplc_conf import generate_all_methods 
from uplc_conf import generate_csv_conf

generate_all_methods(
    isocratic_time=1.0,
    gradient_time=1.0,
    initial_org=20.0,
    output_dir = r"D:\Dongyang.PRO\ACQUDB",
    iteration= 7)

generate_csv_conf(file_name = "auto_test_1", sample_location = "2:48", conf_names ="iteration_7",  output_dir = r"D:\autolynx",index=2)


#name the document in this file