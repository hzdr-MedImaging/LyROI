# LyROI – nnU-Net-based Lymphoma Total Metabolic Tumor Volume Segmentation

> [!IMPORTANT]
> **Regulatory status:** This software and the bundled model are intended **solely for research and development (R&D)**.
> They are **not** intended for primary diagnosis, therapy, or any other clinical decision-making and must **not** be used
> as a medical device.

## Overview

**Ly**mphoma **ROI** prediction framework (**LyROI**) is a collection of neural network models and support tools for
metabolic tumor volume segmentation in (Non-Hodgkin) lymphoma patients in FDG-PET/CT images.

A comprehensive description of development and evaluation of the models is given in the respective [paper](DOI:XXX).
Briefly, the models were trained with the [nnU-Net](https://github.com/MIC-DKFZ/nnUNet) software package. A total of
1192 FDG-PET/CT scans from 716 patients with Non-Hodgkin
lymphoma participating in the [PETAL](https://doi.org/10.1200/jco.2017.76.8093) trial comprised the training dataset.
The ground truth delineation included all lesions (irrespective of size or uptake) that were clinically considered as
lymphoma manifestations by an experienced observer. It was developed iteratively with the assistance of intermediate CNN
models. Accurate contouring of each lesion was achieved by selecting the most appropriate semi-automated delineation
algorithm, manually adjusting its settings, and performing manual corrections when necessary.

Training and testing were performed following a 5-fold cross-validation scheme. Three configurations of the nnU-Net were
used for training: [regular U-Net](https://rodare.hzdr.de/record/4177/files/LyROI_Orig.zip), [medium residual encoder U-Net](https://rodare.hzdr.de/record/4177/files/LyROI_ResM.zip) (8 GB GPU
memory target), and [large residual encoder U-Net](https://rodare.hzdr.de/record/4177/files/LyROI_ResL.zip) (24 GB GPU memory target).
They can be installed as described below and used separately, however, their use in an ensemble (merging individual
outputs via union operation) is recommended to maximize lesion detection sensitivity.

[Scripts](scripts/) subfolder
provides example code snippets to execute the prediction with each model and merge the resulting delineations when using
directly within existing nnU-Net installation. See [manual installation](#manual-installation-and-use) section for more
details.
For simplified workflow, LyROI is also available as a stand-alone tool, see [quick start](#quick-start) section for
usage and installation instructions.

Please cite [nnU-Net](https://www.nature.com/articles/s41592-020-01008-z) and the [following paper](DOI:XXX) when using
LyROI:

```
XXX
```

Special thanks to Prof. Dührsen for the access to the [PETAL](https://doi.org/10.1200/jco.2017.76.8093) trial dataset
for the network training and agreeing to share the resulting models.

## Quick Start

> [!IMPORTANT]
> Working within a dedicated virtual environment (`venv` or `conda`) is highly recommended.

> **Requirements**
> - `python` (>= 3.9)
> - [`pytorch`](https://pytorch.org/get-started/locally/) (>= 2.1.2)

1. Install `python` and `pytorch` (see requirements list above).

   **Note: As of now, torch >=2.9.0 leads to severe performance
   reduction. Earlier versions are recommended.**
2. Install `lyroi` as a package (recommended):
   ```
   pip install lyroi
   ```
   or as modifiable copy (for experienced users):
   ```
   git clone https://github.com/hzdr-MedImaging/LyROI.git
   cd LyROI
   pip install -e .
   ```
3. (OPTIONAL) To change the default model installation directory (default: `$HOME/.lyroi`), set the environment variable
   `LYROI_DIR` to the desired location. See, e.g.
   [here](https://www.freecodecamp.org/news/how-to-set-an-environment-variable-in-linux/) for guidance.
4. Download and install the model files:
    ```
    lyroi_install
    ```
5. Run LyROI for
    - all images in the `input_folder` (see [below](#data-format) for input data format) and output delineation in
      `output_folder`:
       ```
       lyroi -i input_folder -o output_folder
       ```
    - a single patient with CT image `ct.nii.gz` and PET image `pet.nii.gz` (must be coregistered and have the same
      matrix and voxel sizes) and output delineation to `roi.nii.gz`:
      ```
      lyroi -i ct.nii.gz pet.nii.gz -o roi.nii.gz
      ```
   Execution on a GPU-equipped workstation is recommended. In case if no GPU is available, use a flag `-d cpu` to force
   run on a CPU (can be very slow).

## Manual Installation and Use

> **Requirements**
> - `python` (>= 3.9)
> - [`pytorch`](https://pytorch.org/get-started/locally/) (>= 2.1.2)
> - [`nnU-Net`](https://github.com/MIC-DKFZ/nnUNet/blob/dev/documentation/installation_instructions.md) (>= 2.5.2)

1. To download and install the models for each used nnU-Net configuration, execute:
    ```
    nnUNetv2_install_pretrained_model_from_zip https://rodare.hzdr.de/record/4177/files/LyROI_Orig.zip
    nnUNetv2_install_pretrained_model_from_zip https://rodare.hzdr.de/record/4177/files/LyROI_ResM.zip
    nnUNetv2_install_pretrained_model_from_zip https://rodare.hzdr.de/record/4177/files/LyROI_ResL.zip
    ``` 
2. By default, the models will be installed in the folder ``$nnUNet_results/Dataset001_LyROI/``. This might create
   conflicts if you already have a project with the number 001 in your ``$nnUNet_results`` folder. In this case, please
   choose an unoccupied index ``XXX`` for the dataset and rename the LyROI folder to ``DatasetXXX_LyROI``.
3. Download all files in [scripts](scripts/) folder and put them in the same folder. If you changed the dataset index of
   LyROI, edit the [predict.sh](scripts/predict.sh) file and change the ``dataset_id="001"`` line to
   ``dataset_id="XXX"``, where XXX is the new dataset index you selected.
4. Prepare the input data according to the instructions [below](#data-format).
5. Execute ``./predict.sh /path/to/your/folder/input_folder`` and wait for the process to complete. The resulting
   delineations can be found in ``input_folder/pred/`` subfolder. If you want to keep the outputs of the intermediate
   networks, comment out the last line in [predict.sh](scripts/predict.sh)

## Data Format

The input data for batch processing should be presented in the nnU-Net compatible format
(see [here](https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/dataset_format_inference.md) for details).
Only compressed NIfTI (`.nii.gz`) images are currently supported. Corresponding CT and PET volumes must be coregistered
and have the same matrix and voxel sizes.

Input channels:
- `0000` is CT
- `0001` is PET

Here is an example of how the input folder can look like:

```
input_folder
      ├── lymph_20250101_0000.nii.gz
      ├── lymph_20250101_0001.nii.gz
      ├── pat01_0000.nii.gz
      ├── pat01_0001.nii.gz
      ├── rchop001_0000.nii.gz
      ├── rchop001_0001.nii.gz
      ├── ...
```

## Intended Purpose (Non-Medical)

- The software is intended for **algorithmic research, benchmarking, and method exploration** in lymphoma segmentation.
- It is **not intended** to provide information for diagnostic or therapeutic purposes and **must not** be used in
  clinical workflows.
- Do **not** deploy or advertise this software as a medical product or service.

## Disclaimer (Research Use Only – Not a Medical Device)

This software and any bundled or referenced model weights are provided **exclusively for research and development
purposes**. They are **not intended** for use in the diagnosis, cure, mitigation, treatment, or prevention of disease,
or for any other clinical decision-making.

- The software is **not** a medical device and is **not** CE-marked.
- No clinical performance, safety, or effectiveness is claimed or implied.
- Any results must not be used to guide patient management.
- Users are responsible for compliance with all applicable laws, regulations, and data protection requirements when
  processing data.

THE SOFTWARE AND MODELS ARE PROVIDED “AS IS”, WITHOUT ANY WARRANTY, EXPRESS OR IMPLIED.

## Licenses

The **code** in this repository is licensed under **Apache-2.0** (see [`LICENSE`](LICENSE)).  
The **model weights** are licensed under **CC-BY-SA-4.0** (see [`MODEL_LICENSE.md`](MODEL_LICENSE.md)).

## Third-Party Licenses

This project uses or interoperates with the following third-party components:

- **nnU-Net v2** – Copyright © respective authors.
    - License: **Apache-2.0**
- **PyTorch**, **NumPy**, **Nibabel**, etc.
    - Licensed under their respective open-source licenses.

Each third-party component is the property of its respective owners and is provided under its own license terms. Copies
of these licenses are available from the upstream projects.
