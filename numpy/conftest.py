"""
Pytest configuration and fixtures for the Numpy test suite.
"""
from __future__ import division, absolute_import, print_function

import warnings
import pytest
import numpy
import importlib

from numpy.core.multiarray_tests import get_fpu_mode


_old_fpu_mode = None
_collect_results = {}


@pytest.hookimpl()
def pytest_itemcollected(item):
    """
    Check FPU precision mode was not changed during test collection.

    The clumsy way we do it here is mainly necessary because numpy
    still uses yield tests, which can execute code at test collection 
    time.
    """
    global _old_fpu_mode

    mode = get_fpu_mode()

    if _old_fpu_mode is None:
        _old_fpu_mode = mode
    elif mode != _old_fpu_mode:
        _collect_results[item] = (_old_fpu_mode, mode)
        _old_fpu_mode = mode


@pytest.fixture(scope="function", autouse=True)
def check_fpu_mode(request):
    """
    Check FPU precision mode was not changed during the test.
    """
    old_mode = get_fpu_mode()
    yield
    new_mode = get_fpu_mode()

    if old_mode != new_mode:
        raise AssertionError("FPU precision mode changed from {0:#x} to {1:#x}"
                             " during the test".format(old_mode, new_mode))

    collect_result = _collect_results.get(request.node)
    if collect_result is not None:
        old_mode, new_mode = collect_result
        raise AssertionError("FPU precision mode changed from {0:#x} to {1:#x}"
                             " when collecting the test".format(old_mode, 
                                                                new_mode))


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true",
                     default=False, help="run slow tests")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(autouse=True)
def add_np(doctest_namespace):
    doctest_namespace['np'] = numpy


for module, replacement in {
    'numpy.testing.decorators': 'numpy.testing.pytest_tools.decorators',
    'numpy.testing.utils': 'numpy.testing.pytest_tools.utils',
}.items():
    module = importlib.import_module(module)
    replacement = importlib.import_module(replacement)
    module.__dict__.clear()
    module.__dict__.update(replacement.__dict__)
