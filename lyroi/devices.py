from typing import Union, List, Dict


class DeviceInfo:
    def __init__(self,
                 name: str,
                 pretty_name: str,
                 default: bool = False,
                 availability_func: callable = lambda: True):
        self.name = name
        self.pretty_name = pretty_name
        self.default = default
        self.availability_func = availability_func
        self.availability = None # cached value

    def is_available(self):
        if self.availability is None:
            self.availability = self.availability_func()
        return self.availability

    def has_availability(self):
        return self.availability is not None

class DeviceManager:
    def __init__(self):
        # Full info about all operation modes
        self.device_list = {
            "gpu": DeviceInfo(
                name="gpu",
                pretty_name="GPU",
                default=True,
                availability_func=lambda: __import__('torch').cuda.is_available()
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
                default=False,
                availability_func=lambda: __import__('torch').backends.mps.is_available()
            )
        }

    #Helper function to get the pieces of the mode info
    def get_all(self) -> List[str]:
        return list(self.device_list.keys())

    def get_available(self) -> List[str]:
        return [device.name for device in self.device_list.values() if device.is_available()]
        #return self.get_all()

    #Only the first occurrence of default tag will be returned
    def get_default(self, only_available = False) -> str:
        device_list = self.get_available() if only_available else self.get_all()
        for device in device_list:
            if self.device_list[device].default:
                return device
        return "cpu" # fallback

    def get_pretty_name(self, device: str) -> str:
        return self.device_list[device].pretty_name

    def is_available(self, device: str):
        return self.device_list[device].is_available()

    def has_availability(self, device: str):
        return self.device_list[device].has_availability()