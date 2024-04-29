from pathlib import Path
from threading import Event
from typing import Sequence

import pytest

import parsl
from parsl.config import Config
from parsl.dataflow.dependency_resolvers import DEEP_DEPENDENCY_RESOLVER


def local_config():
    return Config(dependency_resolver=DEEP_DEPENDENCY_RESOLVER)


@parsl.python_app
def a(event):
    event.wait()
    return 7


@parsl.python_app
def b(x: int):
    return x + 1


@pytest.mark.local
def test_simple_pos_arg():
    e = Event()
    s = a(e)
    f_b = b(s)
    e.set()

    assert f_b.result() == 8


@parsl.python_app
def b_first(x: Sequence[int]):
    return x[0] + 1


@pytest.mark.local
def test_tuple_pos_arg():
    e = Event()
    s = (a(e),)
    f_b = b_first(s)
    e.set()
    assert f_b.result() == 8


@parsl.python_app
def make_path(s: str):
    return Path(s)


@parsl.python_app
def append_paths(iterable, end_str: str = "end"):
    type_ = type(iterable)
    return type_([Path(s, end_str) for s in iterable])


@pytest.mark.local
@pytest.mark.parametrize(
    "type_",
    [
        tuple,
        list,
        set,
    ],
)
def test_resolving_iterables(type_):
    output1 = make_path("test1")
    output2 = make_path("test2")
    output3 = append_paths(type_([output1, output2]), end_str="end")
    assert output3.result() == type_([Path("test1", "end"), Path("test2", "end")])


@parsl.python_app
def append_paths_dict(iterable: dict, end_str: str = "end"):
    return {Path(k, end_str): Path(v, end_str) for k, v in iterable.items()}


@pytest.mark.local
def test_resolving_dict():
    output1 = make_path("test1")
    output2 = make_path("test2")
    output3 = append_paths_dict({output1: output2}, end_str="end")
    assert output3.result() == {Path("test1", "end"): Path("test2", "end")}



@parsl.python_app
def extract_deep_list(l: list):
    return l[0][0][0][0][0];


@pytest.mark.local
def test_deeper_list():
    e = Event()
    s = a(e)
    f_b = b([[[[[s]]]]])
    assert not f_b.done()

    e.set()

    assert f_b.result() == 7
