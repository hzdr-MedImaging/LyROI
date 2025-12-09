from pathlib import Path
from packaging.version import Version
from lyroi.utils import check_model, install_model, check_setup, setup_lyroi, check_version_local, check_version_online


def predict_petct_entrypoint():
    import argparse
    parser = argparse.ArgumentParser(description='Run lymphoma ROI prediction for the given input folder.')
    parser.add_argument('-i', type=str, required=True,
                        help='Input folder. Remember to use the correct channel specifiers for your files (_0000 for CT'
                             'and _0001 for PET). '
                             'Only .nii.gz files are supported.')
    parser.add_argument('-o', type=str, required=True,
                        help='Output folder. If it does not exist, it will be created. Predicted segmentations will '
                             'have the same name as their source images but without the channel specifiers.')
    parser.add_argument('-m', '--mode', type=str, default='petct', choices=['petct'],
                        help='One of the supported modes of operation. Default: petct')
    parser.add_argument('-d', '--device', type=str, default='gpu', choices=['gpu', 'cpu', 'mps'],
                        help='Computational device to use for prediction. Choose from gpu (default), cpu, and mps.'
                             'To select specific gpu, execute "export CUDA_VISIBLE_DEVICES=..." before running LyROI')
    args = parser.parse_args()
    print("Input:", args.i)
    print("Output:", args.o)
    # import here to accelerate startup
    from lyroi.inference import predict_from_folder
    setup_lyroi()

    assert check_model(args.mode), ("Models for the selected mode of operation have not been installed yet!"
                                    "Run 'lyroi_install " + args.mode + " to download and install the models'")

    if not Path(args.o).exists():
        Path(args.o).mkdir(exist_ok=True, parents=True)

    predict_from_folder(args.i, args.o, args.mode, device='gpu')


def install_model_entrypoint():
    setup_lyroi()

    import argparse
    parser = argparse.ArgumentParser(description='Install the models required for running LyROI in the selected mode')
    parser.add_argument('mode', type=str, choices=['petct'],
                        help='One of the supported modes of operation')
    parser.add_argument('-f', '--force', action='store_true', default=False, help="Force reinstall the"
                                                                                  "model even if it is already installed and up to date.")
    parser.add_argument('-c', '--check', action='store_true', default=False, help="Check if the models are"
                                                                                  "already installed. Does not run the installation process itself")
    args = parser.parse_args()
    print("Selected mode:", args.mode)
    is_installed = check_model(args.mode)
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

    install_model(args.mode)
