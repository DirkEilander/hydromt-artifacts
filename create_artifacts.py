#%%
import hydromt
from hydromt.data_adapter import DataCatalog
import os
from os.path import join, isdir, isfile
from pathlib import Path
import shutil
import tarfile


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=".")


#%% versions and new data
version_old = DataCatalog._version
version_new = "v0.0.4"
print(version_old, version_new)
data_libs = ["data_catalog.yml"]  # paths to new data libs

# make sure names are snake_case
rename = {
    "GDP_world": "gdp_world",
    "GHS-POP_2015": "ghs_pop_2015",
    "GHS-SMOD_2015": "ghs_smod_2015",
    "GHS-SMOD_2015_v2": "ghs-smod_2015_v2",
}

#%% permanent settings
bbox = [11.6, 45.2, 13.00, 46.80]  # Piava river
time_tuple = ("2010-02-01", "2010-02-14")
deltares_root = r"p:/wflow_global"  # root in deltares_data

# old and new folders
src = join(Path.home(), ".hydromt_data", "data", version_old)
dst = join(Path.home(), ".hydromt_data", "data", version_new)

sources_new = list(DataCatalog(data_libs=data_libs).sources.keys()) + list(
    rename.values()
)

#%% download old data to src and copy to dst
data_catalog_old = DataCatalog(artifact_data=version_old)  # triggers download
shutil.copytree(src=src, dst=dst)
# rename original data_catalog

#%% update deltares data yml
data_catalog = DataCatalog(deltares_data=version_old, data_libs=data_libs)
for old, new in rename.items():
    if old in data_catalog.sources:
        data_catalog._sources[new] = data_catalog._sources.pop(old)
data_catalog.to_yml(join(dst, "data_sources_deltares.yml"), root=deltares_root)


# %% export new data to dst; keep old yml file
if isfile(join(dst, "data_catalog.yml")):
    shutil.move(join(dst, "data_catalog.yml"), join(dst, "data_catalog_old.yml"))
data_catalog.export_data(
    data_root=dst, bbox=bbox, time_tuple=time_tuple, source_names=sources_new
)
shutil.move(join(dst, "data_catalog.yml"), join(dst, "data_catalog_tmp.yml"))

#%% combine data_catalog_tmp + data_catalog_old
data_catalog_new = DataCatalog(
    data_libs=[
        join(dst, "data_catalog_old.yml"),
        join(dst, "data_catalog_tmp.yml"),
    ]
)
# remove old names
for old, new in rename.items():
    if old in data_catalog_new.sources:
        data_catalog_new._sources.pop(old)
data_catalog_new.to_yml(join(dst, "data_catalog.yml"))

# %% test
data_catalog_final = DataCatalog(artifact_data=version_new)
for name in data_catalog_final.sources:
    print(name)
    data_catalog_final[name].get_data(bbox=bbox)

#%% clean up tmp and old yml files and make data.tar.gz archive
if isfile(join(dst, "data_catalog_tmp.yml")):
    os.remove(join(dst, "data_catalog_tmp.yml"))
if isfile(join(dst, "data_catalog_old.yml")):
    os.remove(join(dst, "data_catalog_old.yml"))
if isfile(join(dst, "data.tar.gz")):
    os.remove(join(dst, "data.tar.gz"))
# NOTE: manually remove renamed files (if any)

make_tarfile(join(dst, "data.tar.gz"), dst)
#%% FINALLY make a t
