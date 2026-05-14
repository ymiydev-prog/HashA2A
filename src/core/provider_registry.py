from typing import Any
from core.base_provider import BaseDataProvider
from models.schemas import ProviderCapability


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, BaseDataProvider] = {}

    def register(self, provider: BaseDataProvider):
        self._providers[provider.provider_id] = provider

    def get(self, provider_id: str) -> BaseDataProvider | None:
        return self._providers.get(provider_id)

    def list(self) -> list[BaseDataProvider]:
        return list(self._providers.values())

    def list_capabilities(self) -> list[ProviderCapability]:
        return [p.capability for p in self._providers.values()]

    def discover(self) -> list[str]:
        import importlib
        import pkgutil
        import providers as providers_pkg

        discovered = []
        for importer, modname, ispkg in pkgutil.iter_modules(
            providers_pkg.__path__, prefix="providers."
        ):
            if ispkg:
                continue
            try:
                mod = importlib.import_module(modname)
                for attr in dir(mod):
                    obj = getattr(mod, attr)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, BaseDataProvider)
                        and obj is not BaseDataProvider
                    ):
                        self.register(obj())
                        discovered.append(obj.provider_id)
            except Exception:
                pass
        return discovered
