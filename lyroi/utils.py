import json
import os
import requests
import shutil

from pathlib import Path


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

def install_model(mode):
    from nnunetv2.model_sharing.model_download import download_and_install_from_url
    repository_url = get_repository_url()
    ver = check_version_online(mode, repository_url)

    download_links = []
    if mode == 'petct':
        download_links.append(repository_url + "/files/LyROI_Orig.zip")
        download_links.append(repository_url + "/files/LyROI_ResM.zip")
        download_links.append(repository_url + "/files/LyROI_ResL.zip")

    # downloading and installing
    for link in download_links:
        download_and_install_from_url(link)

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
    fold_list = get_folds(mode)
    status = True
    for folder in folder_list:
        status = status and Path(folder, "dataset.json").exists()
        status = status and Path(folder, "plans.json").exists()
        for fold in fold_list:
            status = status and Path(folder, "fold_" + str(fold), "checkpoint_final.pth").exists()
    return status

def validate_extensions(file_list, expected_ext = ".nii.gz"):
    return all([file.endswith(expected_ext) for file in file_list])

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
        print("Creating LyROI directory:" + lyroi_dir)
        Path(lyroi_dir).mkdir(exist_ok=True, parents=True)

    models_dir = get_models_dir()
    if not Path(models_dir).exists():
        Path(models_dir).mkdir(exist_ok=True, parents=True)

    os.environ['nnUNet_raw'] = ""
    os.environ['nnUNet_preprocessed'] = ""
    os.environ['nnUNet_results'] = models_dir # only this one matters

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