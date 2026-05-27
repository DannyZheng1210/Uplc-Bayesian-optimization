import rainbow as rb
def read_chromatogram(chromatogram_rawdata, chromatogram_csv="./"):
    datadir = rb.read(chromatogram_rawdata)
    for f in datadir.datafiles:
        if f.detector == "UV":
            f.export_csv(f"{chromatogram_csv}/uv_data.csv")
            break