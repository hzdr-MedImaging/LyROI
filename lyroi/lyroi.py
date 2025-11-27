
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