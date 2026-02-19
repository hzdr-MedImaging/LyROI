from pathlib import Path
from packaging.version import Version
from lyroi.utils import (check_model, install_model, setup_lyroi, check_version_local, check_version_online,
                         yes_no_input, get_download_size, format_file_size)
from lyroi import __legal__


def predict_petct_entrypoint():
    import argparse
    parser = argparse.ArgumentParser(
        prog = "lyroi",
        description='Run lymphoma ROI prediction for the given input folder',
        epilog=(
            "Examples:\n\n"
            "Segment all volumes in input_dir and save results in output_dir using default mode and gpu device:\n"
            "  lyroi -i input_dir -o output_dir\n\n"
            "Segment ct_img.nii.gz and pet_img.nii.gz volume pair and save results as mask.nii.gz using cpu device at max power:\n"
            "  lyroi -i ct_img.nii.gz pet_img.nii.gz -o mask.nii.gz -d cpu-max\n\n"
            f"{__legal__}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-i', type=str, required=True, nargs='+', metavar="INPUT",
                        help='Input folder or list of files.'
                             'If input folder is specified, please use correct channel specifiers for your files '
                             'according to nnU-Net conventions (_0000 for CT and _0001 for PET). '
                             'If list of files is specified, provide first CT and then PET file. '
                             'Only .nii.gz files are supported.')
    parser.add_argument('-o', type=str, required=True, metavar="OUTPUT",
                        help='Output folder or file, depending on the input mode.'
                             'For folder output, if folder does not exist, it will be created. Predicted segmentations will '
                             'have the same name as their source images but without the channel specifiers.')
    parser.add_argument('-m', '--mode', type=str, default='petct', choices=['petct'], metavar="MODE",
                        help='One of the supported modes of operation: petct (default)')
    parser.add_argument('-d', '--device', type=str, default='gpu', choices=['gpu', 'cpu', 'cpu-max', 'mps'], metavar="DEVICE",
                        help='Computational device to use for prediction. Choose from gpu (default), cpu, cpu-max and mps. '
                             '"cpu" will limit number of cores to 8 while "cpu-max" will use all available cores. "cpu-max" '
                             'mode can be limited by setting "nnUNet_def_n_proc" env variable to desired number of cores. '
                             'To select specific gpu, execute "export CUDA_VISIBLE_DEVICES=..." before running LyROI')

    args = parser.parse_args()

    is_dir_input = False
    if all([Path(i).is_dir() for i in args.i]):
        assert len(args.i) == 1, "Number of input directories > 1 is not supported"
        is_dir_input = True
    is_dir_output = len(Path(args.o).suffix) == 0

    is_file_input = all([Path(i).is_file() for i in args.i])
    is_file_output = len(Path(args.o).suffix) > 0

    dir_mode = is_dir_input and is_dir_output
    file_mode = is_file_input and is_file_output

    if is_dir_input:
        assert is_dir_output, "Output appears to be a file while input is a directory. Input and output types should match!"
    if is_file_input:
        assert is_file_output, "Output appears to be a directory while input is a file (list). Input and output types should match!"
    assert dir_mode != file_mode, "Something is wrong with input/output specifications or inputs do not exist! Please use 'lyroi -h' for help"

    # import here to accelerate startup
    setup_lyroi()
    from lyroi.inference import predict_from_folder, predict_from_files

    if not check_model(args.mode):
        print("The model for the selected mode is not installed or installation is incomplete")
        model_size = format_file_size(get_download_size(args.mode))
        print(f"\nTo download and install the models later, use the following command:\n"
              f"  lyroi_install -m {args.mode}\n\n"
              f"Alternatively, you can install the model now. "
              f"This action will require downloading {model_size} of data from the internet.")
        yes_no_input("\nProceed with the download now", "Download is aborted and the model will not be installed")
        install_model(args.mode)

    assert check_model(args.mode), (f"Something went wrong and the model has not been correctly installed! "
                                    f"Try 'lyroi_install -m {args.mode} -f' to force reinstall the model")

    if dir_mode:
        Path(args.o).mkdir(exist_ok=True, parents=True)
        predict_from_folder(args.i[0], args.o, args.mode, device=args.device)

    if file_mode:
        predict_from_files(args.i, args.o, args.mode, device=args.device)


def install_model_entrypoint():
    setup_lyroi()

    import argparse
    parser = argparse.ArgumentParser(
        prog="lyroi_install",
        description='Install the models required for running LyROI in the selected mode',
        epilog=(
            "Examples:\n\n"
            "Install the models for the default (petct) mode:\n"
            "  lyroi_install\n\n"
            "Check if the models for petct mode are already installed and up to date:\n"
            "  lyroi -c -m petct\n\n"
            f"{__legal__}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-f', '--force', action='store_true', default=False, help="Force reinstall the"
                                                                                  "model even if it is already installed and up to date.")
    parser.add_argument('-c', '--check', action='store_true', default=False, help="Check if the models are"
                                                                                  "already installed. Does not run the installation process itself")
    parser.add_argument('-y', '--yes', action='store_true', default=False, help="Skip the confirmation prompts")
    parser.add_argument('-m', '--mode', type=str, default='petct', choices=['petct'], metavar="MODE",
                        help='Which mode of operation to install the models for: petct (default)')
    args = parser.parse_args()
    print("Selected mode:", args.mode)
    is_installed = check_model(args.mode)

    # check flag handling
    if args.check:
        if is_installed:
            try:
                cur_version = Version(check_version_local(args.mode))
                online_version = Version(check_version_online(args.mode))
                if cur_version == online_version:
                    print("The model is installed and up to date. Current version:", cur_version)
                elif cur_version < online_version:
                    print("The model is installed but there is a newer version available online. Current version:",
                          cur_version, ", newest version:", online_version)
                else:
                    print("The model is installed and it seems to be newer than the newest version available online.",
                          "This should not happen...",
                          "Current version:", cur_version, ", newest version:", online_version)
            except Exception as e:
                print("The model installation is inconsistent:")
                print(e)
        else:
            print("The model is not installed or installation is incomplete")
        return

    try:
        cur_version = check_version_local(args.mode)
        online_version = check_version_online(args.mode)
        up_to_date = cur_version == online_version
    except Exception as e:
        cur_version = "None"
        up_to_date = False

    if is_installed and not args.force and up_to_date:
        print("The installed model is up to date ( version:", cur_version, "). Use flag -f to force reinstall the model.")
        return

    if not args.yes:
        model_size = format_file_size(get_download_size(args.mode))
        print(f"This action will require downloading {model_size} of data from the internet")
        yes_no_input("\nProceed", "Download is aborted and the model will not be installed")
    install_model(args.mode)
