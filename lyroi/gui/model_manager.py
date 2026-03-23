import subprocess

from lyroi.utils import check_version_local, check_version_online, check_model, get_download_size, format_file_size
from lyroi.modes import get_mode_list, get_pretty_name, get_folds, get_suffix_dict


class ModelManager:

    def get_available_models(self):
        return get_mode_list()

    def get_pretty_name(self, model):
        return get_pretty_name(model)

    def get_n_folds(self, model):
        return len(get_folds(model))

    def get_suffix_string(self, model):
        suffixes = get_suffix_dict(model)
        suff_strings = [key + ": " + value for key, value in suffixes.items()]
        return ", ".join(suff_strings)

    def get_installed_version(self, model):
        if not check_model(model):
            return "Not installed"
        try:
            result = check_version_local(model)
            return result
        except Exception:
            return "Corrupted"

    def get_online_version(self, model):
        try:
            result = check_version_online(model)
            return result
        except:
            return "N/A"

    def check_for_updates(self, model) -> str:
        model_name = self.get_pretty_name(model)
        msg = "Do you want to install the \"" + model_name + "\" model?"

        try:
            online_version = check_version_online(model)
        except:
            return "The online repository cannot be reached.\n\nDo you want to try to install the \"" + model_name + "\" model anyway?"

        local_version = self.get_installed_version(model)

        if local_version == "Not installed":
            msg = "The model is currently not installed.\n\n" + msg
        elif local_version == "Corrupted":
            msg = "The current model installation is corrupted. Reinstallation is recommended.\n\n" + msg
        elif local_version == online_version:
            msg = "No updates available.\n\nDo you want to reinstall the \"" + model_name + "\" model?"
        else:
            msg = "New version available: " + online_version + "\n\n" + msg

        model_size = format_file_size(get_download_size(model))
        msg = msg + "\n\n" + "This action will require downloading " + model_size + " of data from the internet"

        return msg
