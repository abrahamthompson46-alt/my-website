"""Compatibility shims for Django on newer Python versions."""

import sys
from copy import copy


def patch_django_context_copy_for_python_314():
    """
    Django 5.1 copies template contexts via copy(super()), which breaks on
    Python 3.14 because super objects became copyable. Fixed upstream in 5.2+.
    """
    if sys.version_info < (3, 14):
        return

    import django

    if django.VERSION >= (5, 2):
        return

    from django.template import context as template_context

    if getattr(template_context.BaseContext.__copy__, "_py314_patched", False):
        return

    def base_context_copy(self):
        duplicate = template_context.BaseContext()
        duplicate.__class__ = self.__class__
        duplicate.__dict__ = copy(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    base_context_copy._py314_patched = True
    template_context.BaseContext.__copy__ = base_context_copy
