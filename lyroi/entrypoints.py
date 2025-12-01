import pathlib
from lyroi.utils import check_model, install_model, check_setup, setup_lyroi

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
    args = parser.parse_args()
    print("Input:", args.i)
    print("Output:", args.o)

    if check_setup():
        print("Setup is correct")
    else:
        print("Setup has not been preformed correctly")

    if not pathlib.Path(args.o).exists():
        pathlib.Path(args.o).mkdir(exist_ok=True, parents=True)

def install_model_entrypoint():
    import argparse
    parser = argparse.ArgumentParser(description='Install the models required for running LyROI in the selected mode')
    parser.add_argument('mode', type=str, choices=['petct'],
                        help='One of the supported modes of operation')
    parser.add_argument('-c', '--check', action='store_true', default=False, help="Check if the models are"
                        "already installed. Does not run the installation process itself")
    args = parser.parse_args()
    print("Selected mode:", args.mode)
    if args.check:
       if check_model(args.mode):
          print("The model is installed")
       else:
          print("The model is not installed")
       return

    setup_lyroi()
    install_model(args.mode)

