"""Provider boundaries route to the same executor; no alternative metric algorithms."""
from .core import Planner

class DemographyProvider:
    status = 'ACTIVE'
    capabilities = ('summary', 'comparison', 'aging')
    def __init__(self, executor): self.executor = executor
    def execute(self, capability, parameters):
        if capability not in self.capabilities: raise ValueError('Unsupported provider capability')
        return self.executor.execute(Planner().plan(capability, parameters))

class HealthcareProximityProvider(DemographyProvider):
    capabilities = ('access', 'coincidence', 'scenario')

class RequiresDataProvider:
    status = 'REQUIRES_DATA'
    def execute(self, *args, **kwargs):
        raise ValueError('Verified data, contract, limitations and human approval required')

class MobilityProvider(RequiresDataProvider): pass
class CapacityProvider(RequiresDataProvider): pass
class DemandProvider(RequiresDataProvider): pass
class HousingProvider(RequiresDataProvider): pass
class EnvironmentProvider(RequiresDataProvider): pass
