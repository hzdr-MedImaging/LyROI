from typing import Union, List, Dict
# from torch.cuda import is_available as cuda_available
# from torch.backends.mps import is_available as mps_available



class DeviceInfo:
    def __init__(self,
                 name: str,
                 pretty_name: str,
                 available: bool = True,
                 default: bool = False):
        self.name = name
        self.pretty_name = pretty_name
        self.available = available
        self.default = default

class DeviceManager:
    def __init__(self):
        # Full info about all operation modes
        self.device_list = {
            "gpu": DeviceInfo(
                name="gpu",
                pretty_name="GPU",
                # available=cuda_available(),
                default=True
            ),
            "cpu": DeviceInfo(
                name="cpu",
                pretty_name="CPU",
                default=False
            ),
            "cpu_max": DeviceInfo(
                name="cpu_max",
                pretty_name="CPU (max speed)",
                default=False
            ),
            "mps": DeviceInfo(
                name="mps",
                pretty_name="MPS (MacOS)",
                # available=mps_available(),
                default=False
            )
        }

    #Helper function to get the pieces of the mode info
    def get_all(self) -> List[str]:
        return list(self.device_list.keys())

    def get_available(self) -> List[str]:
        return self.get_all() # TODO: implement availability check

    #Only the first occurrence of default tag will be returned
    def get_default(self, only_available = False) -> str:
        device_list = self.get_available() if only_available else self.get_all()
        for device in device_list:
            if self.device_list[device].default:
                return device
        return "cpu" # fallback

    def get_pretty_name(self, device: str) -> str:
        return self.device_list[device].pretty_name