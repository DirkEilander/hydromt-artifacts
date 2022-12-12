#%%
import hydromt
from hydromt import DataCatalog
import os
from os.path import join, isdir, isfile
from pathlib import Path
import shutil
import tarfile
import glob


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=".")


#%% versions and new data
version_old = "v0.0.6"
version_new = "v0.0.7"
print(version_old, version_new)

# make sure names are snake_case
# new data sources should be configured in deltares_data.yml
add_sources = ["era5_daily_zarr", "era5_hourly_zarr"]
remove_sources = ["era5", "era5_hourly"]

#%% permanent settings
bbox = [11.6, 45.2, 13.00, 46.80]  # Piava river
time_tuple = ("2010-02-01", "2010-02-14")
deltares_root = r"p:/wflow_global/hydromt"  # root in deltares_data

# old and new folders
src = join(Path.home(), ".hydromt_data", "data", version_old)
dst = join(Path.home(), ".hydromt_data", "data", version_new)

#%% download old data to src and copy to dst
data_catalog_old = DataCatalog(artifact_data=version_old)  # triggers download
shutil.copytree(src=src, dst=dst)
# rename original data_catalog

# %% export new data to dst; keep old yml file
dres_data_catalog = DataCatalog(data_libs="deltares_data.yml")
if isfile(join(dst, "data_catalog.yml")):
    shutil.move(join(dst, "data_catalog.yml"), join(dst, "data_catalog_old.yml"))
dres_data_catalog.export_data(
    data_root=dst, bbox=bbox, time_tuple=time_tuple, source_names=add_sources
)
shutil.move(join(dst, "data_catalog.yml"), join(dst, "data_catalog_tmp.yml"))

#%% combine data_catalog_tmp + data_catalog_old
# NOTE: after running this cell manually inspec the new and old yml files!
data_catalog_new = DataCatalog(
    data_libs=[
        join(dst, "data_catalog_old.yml"),
        join(dst, "data_catalog_tmp.yml"),
    ]
)
# remove old names
for old in remove_sources:
    if old not in data_catalog_new:
        continue
    source = data_catalog_new._sources.pop(old)
    for fn in glob.glob(str(source.path).format(year="*", variable="*", month="*")):
        print(f"removing {fn}")
        os.remove(fn)
data_catalog_new.to_yml(join(dst, "data_catalog.yml"))

# %% test
data_catalog_final = DataCatalog(artifact_data=version_new)
for name in data_catalog_final.sources:
    try:
        data_catalog_final[name].get_data(bbox=bbox)
    except:
        print(name)

#%% clean up tmp and old yml files and make data.tar.gz archive
if isfile(join(dst, "data_catalog_tmp.yml")):
    os.remove(join(dst, "data_catalog_tmp.yml"))
if isfile(join(dst, "data_catalog_old.yml")):
    os.remove(join(dst, "data_catalog_old.yml"))
if isfile(join(dst, "data_sources_deltares.yml")):
    os.remove(join(dst, "data_sources_deltares.yml"))
if isfile(join(dst, "data.tar.gz")):
    os.remove(join(dst, "data.tar.gz"))
for fn in glob.glob(join(dst, "*.py")):
    os.remove(fn)
# NOTE: manually remove renamed files (if any)

make_tarfile(join(dst, "data.tar.gz"), dst)
#%% FINALLY 
# update changelog!
# publish the release online
