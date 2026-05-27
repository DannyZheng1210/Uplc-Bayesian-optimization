import rainbow as rb

datadir = rb.read("phenyl_LHS5.raw")
for f in datadir.datafiles:
    if f.detector == "UV":
        f.export_csv("uv_data.csv")
        breaki