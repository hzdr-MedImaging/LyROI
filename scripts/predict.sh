#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Command requires 1 argument (input dir). Destination dir will be a \'pred\' subfolder of it. Only run within nnUNet enviroment"
    exit 1
fi

dataset_id="001"

inpDir=$1
outDir1=$inpDir"/pred_nnUnet"
outDir2=$inpDir"/pred_nnUnetResM"
outDir3=$inpDir"/pred_nnUnetResL"
mergeDir=$inpDir"/pred"


nnUNetv2_predict -i $inpDir -o $outDir1 -d $dataset_id -p nnUNetPlans -c 3d_fullres --continue_prediction
nnUNetv2_predict -i $inpDir -o $outDir2 -d $dataset_id -p nnUNetResEncUNetMPlans -c 3d_fullres --continue_prediction
nnUNetv2_predict -i $inpDir -o $outDir3 -d $dataset_id -p nnUNetResEncUNetLPlans -c 3d_fullres --continue_prediction

python merge_delinations.py $mergeDir $outDir1 $outDir2 $outDir3

rm -rf $outDir1 $outDir2 $outDir3