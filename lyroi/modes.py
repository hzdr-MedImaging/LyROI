from typing import Union, List, Dict

class ModeInfo:
    def __init__(self,
                 name: str,
                 pretty_name: str,
                 folds: List[Union[int, str]],
                 model_plans: List[str],
                 model_config: str,
                 suffixes: Dict[str, str],
                 archive_names: List[str]):
        self.name = name
        self.pretty_name = pretty_name
        self.folds = folds
        self.suffixes = suffixes
        self.model_plans = model_plans
        self.model_config = model_config
        self.archive_names = archive_names

# Full info about all operation modes
mode_list = {
    "petct": ModeInfo(
        name="petct",
        pretty_name="PET/CT",
        folds=[0, 1, 2, 3, 4],
        model_plans=["nnUNetPlans", "nnUNetResEncUNetMPlans", "nnUNetResEncUNetLPlans"],
        model_config="3d_fullres",
        suffixes={"CT": "_0000",
                  "PET": "_0001"},
        archive_names=["LyROI_Orig.zip", "LyROI_ResM.zip", "LyROI_ResL.zip"]
    )
}

#Helper function to get the pieces of the mode info
def get_mode_list() -> List[str]:
    return list(mode_list.keys())

def get_pretty_name(mode: str) -> str:
    return mode_list[mode].pretty_name

def get_model_folders(mode: str) -> List[str]:
    from nnunetv2.utilities.file_path_utilities import get_output_folder

    mode_info = mode_list[mode]
    folder_list = [get_output_folder(1, 'nnUNetTrainer', plan, mode_info.model_config) for plan in mode_info.model_plans]
    return folder_list

def get_folds(mode: str) -> List[Union[int, str]]:
    return mode_list[mode].folds

def get_suffixes(mode: str) -> List[str]:
    return list(mode_list[mode].suffixes.values())

def get_archive_names(mode: str):
    return mode_list[mode].archive_names