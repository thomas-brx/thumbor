from derpconf.config import Config
from tc_core import Extension, Extensions

Config.define('FALLBACK_LOADER_BASE_LOADER', 'thumbor.loaders.http_loader', 'Fallback loader', 'FallbackLoader')
extension = Extension('fallback_loader')
