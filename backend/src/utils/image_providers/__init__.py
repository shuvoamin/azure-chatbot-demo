from utils.model_registry import ImageRegistry
from utils.image_providers.azure_flux import create_azure_flux_provider

def register_builtin_image_providers():
    ImageRegistry.register("azure-flux", create_azure_flux_provider)

register_builtin_image_providers()
