import subprocess
from lyroi.utils import check_version_local, check_version_online, check_model, get_model_dict


class ModelManager:

    def get_available_models(self):
        models = get_model_dict()
        return list(models.keys())

    def get_pretty_name(self, model):
        models = get_model_dict()
        return models[model]

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
