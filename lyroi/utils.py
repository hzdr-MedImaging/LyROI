import json
import os
import sys
import math
import requests
import psutil

from pathlib import Path


def format_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    str_time = "%.3f s" % seconds
    if minutes > 0:
        str_time = "%d min " % minutes + str_time
    if hours > 0:
        str_time = "%d h " % hours + str_time
    return str_time


def validate_extensions(file_list, expected_ext = ".nii.gz"):
    return all([file.endswith(expected_ext) for file in file_list])

def yes_no_input(prompt, no_message):
    answer = input(prompt + " ([y]/n)? ")
    if answer.lower() in ['y', 'yes', '']:
        return
    elif answer.lower() in ['n', 'no']:
        print(no_message)
        sys.exit(0)
    else:
        print("Incorrect input, try again")
        yes_no_input(prompt, no_message)

# taken from https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
def format_file_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def get_model_dict():
    models = {
        "petct": "PET/CT"
    }
    return models

def get_model_folders(mode):
    from nnunetv2.utilities.file_path_utilities import get_output_folder
    folder_list = []
    if mode == 'petct':
        folder_list.append(
            get_output_folder(1, 'nnUNetTrainer', 'nnUNetPlans', '3d_fullres')
        )
        folder_list.append(
            get_output_folder(1, 'nnUNetTrainer', 'nnUNetResEncUNetMPlans', '3d_fullres')
        )
        folder_list.append(
            get_output_folder(1, 'nnUNetTrainer', 'nnUNetResEncUNetLPlans', '3d_fullres')
        )
    return folder_list

def get_folds(mode):
    folds = []
    if mode == 'petct':
        folds = [0, 1, 2, 3, 4]
    if mode == 'petct_turbo':
        folds = ['all']
    return folds

def get_suffixes(mode):
    suffixes = []
    if mode == 'petct':
        suffixes = ['_0000', '_0001']
    if mode == 'petct_turbo':
        suffixes = ['_0000', '_0001']
    return suffixes

def get_repository_url():
    try:
        # collection of sources. Should automatically resolve to the latest versions of the models
        r = requests.head("https://rodare.hzdr.de/record/4160", allow_redirects=True)
        return r.url
    except Exception as e:
        exit("Cannot reach the online model repository! Please check your internet connection or contact the developer.")

def get_download_urls(mode, repository_url = None):
    if repository_url is None:
        repository_url = get_repository_url()

    download_urls = []
    if mode == 'petct':
        download_urls.append(repository_url + "/files/LyROI_Orig.zip")
        download_urls.append(repository_url + "/files/LyROI_ResM.zip")
        download_urls.append(repository_url + "/files/LyROI_ResL.zip")
    return download_urls

def get_download_size(mode):
    download_urls = get_download_urls(mode)
    try:
        size = 0
        for url in download_urls:
            r = requests.head(url)
            size += int(r.headers['content-length'])
        return size
    except Exception as e:
        exit("Cannot locate the model files! Please check your internet connection or contact the developer.")

def install_model(mode):
    from nnunetv2.model_sharing.model_download import download_and_install_from_url
    repository_url = get_repository_url()
    ver = check_version_online(mode, repository_url)

    # downloading and installing
    download_urls = get_download_urls(mode, repository_url)
    print("Wait until all downloads are finished")
    for url in download_urls:
        download_and_install_from_url(url)

    # writing a current version
    model_folders = get_model_folders(mode)
    for folder in model_folders:
        Path(folder, "VERSION").write_text(ver)

def check_version_online(mode, repository_url = None):
    if repository_url is None:
        repository_url = get_repository_url()
    try:
        r = requests.get(repository_url + "/files/VERSION")
        version_file = r.content.decode("utf-8")
        j_file = json.loads(version_file)
        return j_file[mode]
    except Exception as e:
        exit("Cannot find version info in the online model repository! Please contact the developer.")

def check_version_local(mode):
    version_list = []
    model_folders = get_model_folders(mode)
    for folder in model_folders:
        if Path(folder, "VERSION").exists():
            version_list.append(Path(folder, "VERSION").read_text())
        else:
            version_list.append(None)
    uniques = set(version_list)

    if None in uniques:
        raise Exception("One or more submodels are missing the version information!")
    if len(uniques) > 1:
        raise Exception("Versions mismatch between the submodels!")

    return uniques.pop()

def check_model(mode):
    try:
        folder_list = get_model_folders(mode)
    except Exception as e:
        return False
    if len(folder_list) == 0:
        return False
    fold_list = get_folds(mode)
    status = True
    for folder in folder_list:
        status = status and Path(folder, "dataset.json").exists()
        status = status and Path(folder, "plans.json").exists()
        for fold in fold_list:
            status = status and Path(folder, "fold_" + str(fold), "checkpoint_final.pth").exists()
    return status

def get_lyroi_dir():
    if 'LYROI_DIR' in os.environ:
        return os.environ['LYROI_DIR']
    else:
        return str(Path(Path.home() , '.lyroi')) #default

def get_models_dir():
    return str(Path(get_lyroi_dir(), "nnUNet_results"))

def get_tmp_dir():
    return str(Path(get_lyroi_dir(), "tmp"))

def check_setup():
    status = True
    lyroi_dir = get_lyroi_dir()
    models_dir = get_models_dir()
    status = status and Path(lyroi_dir).exists()
    status = status and 'nnUNet_raw' in os.environ
    status = status and 'nnUNet_preprocessed' in os.environ
    status = status and 'nnUNet_results' in os.environ
    status = status and Path(lyroi_dir) in Path(models_dir).parents
    return status

def setup_lyroi():
    lyroi_dir = get_lyroi_dir()
    if not Path(lyroi_dir).exists():
        print("Creating LyROI directory: " + lyroi_dir)
        Path(lyroi_dir).mkdir(exist_ok=True, parents=True)

    models_dir = get_models_dir()
    if not Path(models_dir).exists():
        Path(models_dir).mkdir(exist_ok=True, parents=True)

    os.environ['nnUNet_raw'] = models_dir
    os.environ['nnUNet_preprocessed'] = models_dir
    os.environ['nnUNet_results'] = models_dir # only this one matters
    # some performance tweeks:
    os.environ['nnUNet_def_n_proc'] =(
        str(psutil.cpu_count(logical=False))) if 'nnUNet_def_n_proc' not in os.environ \
        else str(os.environ['nnUNet_def_n_proc'])
    os.environ['OMP_NUM_THREADS'] = str(psutil.cpu_count(logical=False))
    os.environ['MKL_NUM_THREADS'] = str(psutil.cpu_count(logical=False))
    os.environ['OMP_PROC_BIND'] = "close"
    os.environ['OMP_PLACES'] = "cores"
    os.environ['OMP_SCHEDULE'] = "static"
    os.environ['GOMP_CPU_AFFINITY '] = "N-M"


if __name__ == "__main__":
    setup_lyroi()
    print(os.environ['nnUNet_results'])
    print("All correct:", check_setup())
    print("Model found:", check_model("petct"))
    print("Online version:", check_version_online("petct"))
    try:
        version = check_version_local("petct")
        print("Local version:", version)
    except Exception as e:
        print(e)