"""Mixins to compose customers and service stations with :func:`~openqtsim.core.utils.create_object`."""

from .misc import Identifiable, ExtraMetadata
from .resource import HasResource, HasLength
from .customer import HasArrivalSchedule, HasHandlingTimes, HasMaxWait
