import rainbow as rb
import os

def read_chromatogram(chromatogram_rawdata, chromatogram_csv="./", wavelength=254):
    datadir = rb.read(chromatogram_rawdata)
    
    base_name = os.path.splitext(os.path.basename(chromatogram_rawdata))[0]
    output_path = os.path.join(chromatogram_csv, f"{base_name}.csv")
    
    for f in datadir.datafiles:
        if f.detector == "UV":
            f.export_csv(output_path, labels=wavelength) 
            break


read_chromatogram("phenyl_LHS5.raw", wavelength=254)    # one wavelength: 254nm
# read_chromatogram("phenyl_LHS5.raw", chromatogram_csv="./", wavelength=[254, 280])  # multiple wavelengths