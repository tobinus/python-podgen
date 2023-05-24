from __future__ import absolute_import

import warnings

def deprecated(deprecated_since, removed_in, description):
    """Decorator for marking functions as deprecated. It wraps and copies name
    and documentation of the decorated function. This decorator only allows for
    deprecation of functions.

    :param deprecated_since:    Version in which the function was deprecated.
    :param removed_in:          Version in which the function is to be removed.
    :param description:         Description of the deprecation.
    :returns:                   Decorated function.
    """

    def deprecation_decorator(func):
        def func_wrapper(*args, **kwargs):
            deprecation_warning(
                func.__name__,
                deprecated_since,
                removed_in,
                description)
            return func(*args, **kwargs)

        # Hide the decorator by taking the decorated functions name and docs.
        func_wrapper.__name__ = func.__name__
        func_wrapper.__doc__ = func.__doc__
        return func_wrapper
    return deprecation_decorator

def deprecation_warning(
    deprecated_name,
    deprecated_since,
    removed_in,
    description):

    warnings.warn\
        (
            "{} is deprecated as of {} and will be removed in {}. {}" \
                .format(deprecated_name, deprecated_since, removed_in, \
                    description),
            category=DeprecationWarning,
            stacklevel=2
        )
