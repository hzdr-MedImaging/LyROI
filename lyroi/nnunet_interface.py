# Parts taken and modified after https://github.com/MIC-DKFZ/nnUNet/

import torch
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor


def get_torch_device(device='gpu'):
    assert device in ['cpu', 'gpu',
                      'mps'], f'-device must be either cpu, mps or cuda. Other devices are not tested/supported. Got: {device}.'
    if device == 'cpu':
        # let's allow torch to use hella threads
        import multiprocessing
        torch.set_num_threads(multiprocessing.cpu_count())
        device = torch.device('cpu')
    elif device == 'gpu':
        # multithreading in torch doesn't help nnU-Net if run on GPU
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        device = torch.device('cuda')
    else:
        device = torch.device('mps')

    return device

def nnunet_predict(input_folder, output_folder, model_folder, folds, torch_device):

    predictor = nnUNetPredictor(tile_step_size=0.5,
                                use_gaussian=True,
                                use_mirroring=True,
                                perform_everything_on_device=True,
                                device=torch_device,
                                verbose=False,
                                verbose_preprocessing=False,
                                allow_tqdm=True)

    predictor.initialize_from_trained_model_folder(
        model_folder,
        folds,
        checkpoint_name='checkpoint_final.pth'
    )
    predictor.predict_from_files(str(input_folder), str(output_folder),
                                 save_probabilities=False,
                                 overwrite=True,
                                 num_processes_preprocessing=3,
                                 num_processes_segmentation_export=3,
                                 folder_with_segs_from_prev_stage=None,
                                 num_parts=1,
                                 part_id=0)