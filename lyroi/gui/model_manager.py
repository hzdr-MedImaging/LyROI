import subprocess
from lyroi.utils import check_version_local, check_version_online, check_model
from lyroi.modes import get_mode_list, get_pretty_name


class ModelManager:

    def get_available_models(self):
        return get_mode_list()

    def get_pretty_name(self, model):
        return get_pretty_name(model)

    def get_installed_version(self, model):
        if not check_model(model):
            return "Not installed"
        try:
            result = check_version_local(model)
            return result
        except Exception:
            return "Corrupted"

    def check_for_updates(self, model):
        try:
            online_version = check_version_online(model)
        except:
            return "Online repository cannot be reached"
        try:
            local_version = check_version_local(model)
        except:
            local_version = "0.0.0"

        if local_version == online_version:
            return "No updates available"
        else:
            return "New version available: " + online_version
