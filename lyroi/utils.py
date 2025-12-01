import os
import pathlib


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

def install_model(mode):
    from nnunetv2.model_sharing.model_download import download_and_install_from_url
    download_links = []
    if mode == 'petct':
        download_links.append("https://rodare.hzdr.de/record/4161/files/LyROI_Orig.zip")
        download_links.append("https://rodare.hzdr.de/record/4161/files/LyROI_ResM.zip")
        download_links.append("https://rodare.hzdr.de/record/4161/files/LyROI_ResL.zip")

    for link in download_links:
        download_and_install_from_url(link)

def check_model(mode):
    folder_list = get_model_folders(mode)
    fold_list = get_folds(mode)
    status = True
    for folder in folder_list:
        status = status and pathlib.Path(folder, "dataset.json").exists()
        status = status and pathlib.Path(folder, "plans.json").exists()
        for fold in fold_list:
            status = status and pathlib.Path(folder, "fold_" + str(fold), "checkpoint_final.pth").exists()


    return status


def get_lyroi_dir():
    if 'LYROI_DIR' in os.environ:
        return os.environ['LYROI_DIR']
    else:
        return str(pathlib.Path(pathlib.Path.home() , '.lyroi')) #default

def get_models_dir():
    return str(pathlib.Path(get_lyroi_dir(), "nnUNet_results"))

def check_setup():
    status = True
    lyroi_dir = get_lyroi_dir()
    models_dir = get_models_dir()
    status = status and pathlib.Path(lyroi_dir).exists()
    status = status and 'nnUNet_raw' in os.environ
    status = status and 'nnUNet_preprocessed' in os.environ
    status = status and 'nnUNet_results' in os.environ
    status = status and pathlib.Path(lyroi_dir) in pathlib.Path(models_dir).parents
    return status

def setup_lyroi():
    lyroi_dir = get_lyroi_dir()
    if not pathlib.Path(lyroi_dir).exists():
        print("Creating LyROI directory:" + lyroi_dir)
        pathlib.Path(lyroi_dir).mkdir(exist_ok=True, parents=True)

    models_dir = get_models_dir()
    if not pathlib.Path(models_dir).exists():
        pathlib.Path(models_dir).mkdir(exist_ok=True, parents=True)

    os.environ['nnUNet_raw'] = ""
    os.environ['nnUNet_preprocessed'] = ""
    os.environ['nnUNet_results'] = models_dir # only this one matters

if __name__ == "__main__":
    setup_lyroi()
    print(os.environ['nnUNet_results'])
    print("All correct: ", check_setup())
    print("Model found:", check_model("petct"))