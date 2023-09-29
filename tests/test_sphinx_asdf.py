import os
import pickle
from pathlib import Path
from tempfile import gettempdir

import pytest
from docutils import nodes

from sphinx_asdf import nodes as sa_nodes


@pytest.fixture(scope="session")
def rootdir():
    return Path(__file__).parent.absolute() / "roots"


@pytest.fixture(scope="session")
def sphinx_test_tempdir():
    """
    temporary directory that wrapped with `path` class.
    """

    def make_tmpdir():
        return os.path.join(gettempdir(), str(os.getpid()))

    return Path(os.environ.get("SPHINX_TEST_TEMPDIR", make_tmpdir())).absolute()


@pytest.mark.sphinx("dummy", testroot="basic-generation")
def test_basic_generation(app, status, warning):
    app.builder.build_all()

    foo_doc = app.srcdir / "generated" / "foo.rst"
    assert foo_doc.exists()
    assert (".. asdf-schema::\n" "    :schema_root: schemas\n" "\n" "    foo\n") in foo_doc.read_text()

    bar_doc = app.srcdir / "generated" / "bar.rst"
    assert bar_doc.exists()
    assert (".. asdf-schema::\n" "    :schema_root: schemas\n" "\n" "    bar\n") in bar_doc.read_text()

    baz_doc = app.srcdir / "generated" / "core" / "baz.rst"
    assert baz_doc.exists()
    assert (".. asdf-schema::\n" "    :schema_root: schemas\n" "\n" "    core/baz\n") in baz_doc.read_text()


@pytest.mark.sphinx("dummy", testroot="global-config")
def test_generation_global_config(app, status, warning):
    app.builder.build_all()

    foo_doc = app.srcdir / "generated" / "foo.rst"
    assert foo_doc.exists()
    assert (".. asdf-schema::\n" "    :schema_root: a/b/c/schemas\n" "\n" "    foo\n") in foo_doc.read_text()

    bar_doc = app.srcdir / "generated" / "bar.rst"
    assert bar_doc.exists()
    assert (".. asdf-schema::\n" "    :schema_root: a/b/c/schemas\n" "\n" "    bar\n") in bar_doc.read_text()

    baz_doc = app.srcdir / "generated" / "core" / "baz.rst"
    assert baz_doc.exists()
    assert (".. asdf-schema::\n" "    :schema_root: a/b/c/schemas\n" "\n" "    core/baz\n") in baz_doc.read_text()


@pytest.mark.sphinx("dummy", testroot="global-prefix")
def test_generation_global_prefix(app, status, warning):
    app.builder.build_all()

    foo_doc = app.srcdir / "generated" / "a" / "b" / "c" / "foo.rst"
    assert foo_doc.exists()
    assert (
        ".. asdf-schema::\n" "    :standard_prefix: a/b/c\n" "    :schema_root: schemas\n" "\n" "    foo\n"
    ) in foo_doc.read_text()

    bar_doc = app.srcdir / "generated" / "a" / "b" / "c" / "bar.rst"
    assert bar_doc.exists()
    assert (
        ".. asdf-schema::\n" "    :standard_prefix: a/b/c\n" "    :schema_root: schemas\n" "\n" "    bar\n"
    ) in bar_doc.read_text()

    baz_doc = app.srcdir / "generated" / "a" / "b" / "c" / "core" / "baz.rst"
    assert baz_doc.exists()
    assert (
        ".. asdf-schema::\n" "    :standard_prefix: a/b/c\n" "    :schema_root: schemas\n" "\n" "    core/baz\n"
    ) in baz_doc.read_text()


@pytest.mark.sphinx("dummy", testroot="basic-generation")
def test_basic_build(app, status, warning):
    app.builder.build_all()

    # Test each of the generated schema documents
    for name in ["foo", "bar", "core/baz"]:
        doctree_path = app.doctreedir / "generated" / f"{name}.doctree"
        doc = pickle.loads(doctree_path.read_bytes())  # noqa: S301

        title = next(iter(doc.findall(nodes.title)))
        assert title.astext() == name

        schema_top = list(doc.findall(sa_nodes.schema_doc))
        assert len(schema_top) > 0
