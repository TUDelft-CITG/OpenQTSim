"""General-purpose mixins (recreated locally, following OpenCLSim/OpenTNSim conventions)."""

import uuid


class Identifiable:
    """Mixin class: give the object a name and a unique id.

    Parameters
    ----------
    name : str
        Name of the object (e.g. the vessel name).
    id : str, optional
        Unique identifier; a random UUID is generated when omitted.

    Attributes
    ----------
    name : str
        Name of the object.
    id : str
        Unique identifier.

    Raises
    ------
    ValueError
        If name is not a nonempty string.
    """

    def __init__(self, *args, name, id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a nonempty string.")
        self.name = name
        self.id = id if id is not None else str(uuid.uuid4())


class ExtraMetadata:
    """Mixin class: store all leftover keyword arguments in the metadata property (use as last mixin).

    Parameters
    ----------
    **kwargs
        Leftover keyword arguments.

    Attributes
    ----------
    metadata : dict
        The leftover keyword arguments.

    Raises
    ------
    TypeError
        If ExtraMetadata is not the last mixin.
    """

    def __init__(self, *args, **kwargs):
        mro = type(self).__mro__
        if mro[mro.index(ExtraMetadata) + 1] is not object:
            raise TypeError("ExtraMetadata must be the last mixin of {}.".format(type(self).__name__))
        super().__init__(*args)
        self.metadata = kwargs
