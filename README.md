# LyROI – nnU-Net-based Lymphoma Total Metabolic Tumor Volume Segmentation Tool

> [!IMPORTANT]
> **Regulatory status:** This software and the bundled model are intended **solely for research and development (R&D)**.  
> They are **not** intended for diagnosis, therapy, or any other clinical decision-making and must **not** be used as a medical device.

## Overview
This repository provides a lightweight tool and configuration to run inference with a bundled **nnU-Net v2**-based segmentation model.  
The **code** in this repository is licensed under **Apache-2.0** (see `LICENSE`).  
The **model weights** are licensed **separately** (see `MODEL_LICENSE.md`) because their terms depend on the training data’s rights.

## Intended Purpose (Non-Medical)
- The software is intended for **algorithmic research, benchmarking, and method exploration** in lymphoma segmentation.
- It is **not intended** to provide information for diagnostic or therapeutic purposes and **must not** be used in clinical workflows.
- Do **not** deploy or advertise this software as a medical product or service.

## Quick Start
> Prerequisites: Python 3.9+ and a working CUDA stack (optional, for GPU inference).

TBD

## Disclaimer (Research Use Only – Not a Medical Device)

This software and any bundled or referenced model weights are provided **exclusively for research and development purposes**. They are **not intended** for use in the diagnosis, cure, mitigation, treatment, or prevention of disease, or for any other clinical decision-making.

- The software is **not** a medical device and is **not** CE-marked.
- No clinical performance, safety, or effectiveness is claimed or implied.
- Any results must not be used to guide patient management.
- Users are responsible for compliance with all applicable laws, regulations, and data protection requirements when processing data.

THE SOFTWARE AND MODELS ARE PROVIDED “AS IS”, WITHOUT ANY WARRANTY, EXPRESS OR IMPLIED.

## Third-Party Licenses

This project uses or interoperates with the following third-party components:

- **nnU-Net v2** – Copyright © respective authors.
  - License: Apache-2.0
- **PyTorch**, **NumPy**, **Nibabel**, etc.
  - Licensed under their respective open-source licenses.

Each third-party component is the property of its respective owners and is provided under its own license terms. Copies of these licenses are available from the upstream projects.
