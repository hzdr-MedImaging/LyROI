import time
import nibabel as nib
import numpy as np

from lyroi.utils import get_model_folders, get_folds, get_tmp_dir, get_suffixes, validate_extensions
from lyroi.nnunet_interface import nnunet_predict, get_torch_device
from pathlib import Path
from shutil import move

def merge_delineations(input_folders, output_folder, strategy="u", force = True):
    assert strategy in ["u", "i", "m"], "Invalid merging strategy"

    input_files = [list(Path(input_dir).glob("*.nii.gz")) for input_dir in input_folders]
    assert len(set([len(l) for l in input_files])) == 1, "Number of images in the submodel output folders do not match. Something went wrong with the predictions"

    input_basenames = [[input_file.name for input_file in input_folder] for input_folder in input_files]
    __ = [input_dir.sort() for input_dir in input_basenames]  # sort lists
    assert input_basenames.count(input_basenames[0]) == len(input_basenames), "Files in the submodel output folders do not match. Something went wrong with the predictions"

    for file_name in input_basenames[0]:
        files_in = [Path(input_dir, file_name) for input_dir in input_folders]
        file_out = Path(output_folder, file_name)

        if file_out.exists():
            if force:
                file_out.unlink()
            else:
                raise FileExistsError(f"Output file {file_out} already exists!")

        if len(files_in) == 1:
            # no need to merge anything. Just move files
            move(files_in[0], file_out)
        else:
            # okay, now we actually need to read files and save results
            imgs_in = [nib.load(file) for file in files_in]
            vols_in = [nifti.get_fdata() for nifti in imgs_in]

            if strategy == "u":
                result = np.logical_or.reduce(vols_in)
            if strategy == "i":
                result = np.logical_and.reduce(vols_in)
            if strategy == "m":
                result = np.average(vols_in, axis=0) > 0.5
            nifti_out = nib.Nifti1Image(result.astype(np.uint8), affine=imgs_in[0].affine, header=imgs_in[0].header)
            nib.save(nifti_out, file_out)

def check_inputs(input_folder, mode):
    suffixes = get_suffixes(mode)

    if len(suffixes) == 1:
        return True

    suffixes = [suffix + ".nii.gz" for suffix in suffixes]
    input_lists = [list(Path(input_folder).glob("*"+ suffix)) for suffix in suffixes]
    input_ids = [[input_file.name.removesuffix(suffix) for input_file in input_list] for input_list, suffix in zip(input_lists, suffixes)]

    unpaired = (set(input_ids[0]) - set(input_ids[1])) | (set(input_ids[1]) - set(input_ids[0]))
    if len(unpaired) == 0:
        return True
    else:
        names = "\n".join(unpaired)
        exit("Cannot proceed, the following patients are missing either CT or PET:\n" + names)

def transfer_input_files(input_files, target_folder, mode, pname = 'patient_001'):
    suffixes = get_suffixes(mode)
    n_channels = len(suffixes)
    if len(input_files) != n_channels:
        exit(f"Number of input files does not match the number of input channels for the selected mode ({n_channels})")
    for input_file, suffix in zip(input_files, suffixes):
        Path(target_folder, pname + suffix + ".nii.gz").symlink_to(input_file)

def transfer_output_files(input_folder, output_file, pname = 'patient_001'):
    Path(output_file).unlink(missing_ok=True)
    move(Path(input_folder, pname + ".nii.gz"), output_file)

def predict_from_folder(input_folder, output_folder, mode, device='gpu'):
    check_inputs(input_folder, mode)

    model_folders = get_model_folders(mode)
    folds = get_folds(mode)
    tmp_dir = get_tmp_dir()
    tmp_rundir = Path(tmp_dir, str(time.time_ns()))
    tmp_subdirs = []

    print("Starting predictions. Wait until all models finish prediction to see the results")
    torch_device = get_torch_device(device)
    try:
        counter = 0
        for folder in model_folders:
            counter += 1
            print(f"Predicting with model {counter}/{len(model_folders)}")
            tmp_subdir = Path(tmp_rundir, Path(folder).stem)
            tmp_subdirs.append(tmp_subdir)
            nnunet_predict(input_folder, tmp_subdir, folder, folds, torch_device)
        print("Merging delineations...")
        merge_delineations(tmp_subdirs, output_folder)
    except Exception as e:
        print("Execution halted: ", e.args[0])
        raise e
    finally:
        for tmp_subdir in tmp_subdirs:
            for file in tmp_subdir.iterdir():
                file.unlink()
            tmp_subdir.rmdir()
        tmp_rundir.rmdir()
        try:
            tmp_dir.rmdir()
        except Exception:
            pass

def predict_from_files(input_files, output_file, mode, device='gpu'):
    validate_extensions(input_files + [output_file], ".nii.gz")

    tmp_dir = get_tmp_dir()
    tmp_rundir = Path(tmp_dir, str(time.time_ns()))
    tmp_input_dir = Path(tmp_rundir, "input")
    tmp_output_dir = Path(tmp_rundir, "output")
    try:
        tmp_input_dir.mkdir(exist_ok=True, parents=True)
        tmp_output_dir.mkdir(exist_ok=True, parents=True)
        transfer_input_files(input_files, tmp_input_dir, mode)
        predict_from_folder(tmp_input_dir, tmp_output_dir, mode, device)
        transfer_output_files(tmp_output_dir, output_file)
    except Exception as e:
        print("Execution halted: ", e.args[0])
        raise e
    finally:
        for file in tmp_input_dir.iterdir():
            file.unlink()
        for file in tmp_output_dir.iterdir():
            file.unlink()
        tmp_input_dir.rmdir()
        tmp_output_dir.rmdir()
        tmp_rundir.rmdir()
        try:
            tmp_dir.rmdir()
        except Exception:
            pass
