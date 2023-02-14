from importlib import import_module
from thumbor.loaders.file_loader import load as file_load
from thumbor.utils import logger


original_loader_module = None

async def load(context, path):
    global original_loader_module
    if original_loader_module is None:
        original_loader_module = import_module(context.config.get('FALLBACK_LOADER_BASE_LOADER', None))

    result = await original_loader_module.load(context, path)

    if result.successful == False:
        return await file_load(context, '404.png')
    return result
