import os
import pickle

import pytest
from tempfile import gettempdir

from docutils import nodes
from sphinx.testing.path import path

from sphinx_asdf import nodes as sa_nodes


@pytest.fixture(scope='session')
def rootdir():
    return path(__file__).parent.abspath() / 'roots'


@pytest.fixture(scope='session')
def sphinx_test_tempdir():
    """
    temporary directory that wrapped with `path` class.
    """
    def make_tmpdir():
        return os.path.join(gettempdir(), str(os.getpid()))
    return path(os.environ.get('SPHINX_TEST_TEMPDIR', make_tmpdir())).abspath()


@pytest.mark.sphinx('dummy', testroot='basic-generation')
def test_basic_generation(app, status, warning):
    app.builder.build_all()

    foo_doc = (app.srcdir / 'generated' / 'foo.rst')
    assert foo_doc.exists()
    assert ('.. asdf-schema::\n'
            '    :schema_root: schemas\n'
            '\n'
            '    foo\n') in foo_doc.text()

    bar_doc = (app.srcdir / 'generated' / 'bar.rst')
    assert bar_doc.exists()
    assert ('.. asdf-schema::\n'
            '    :schema_root: schemas\n'
            '\n'
            '    bar\n') in bar_doc.text()

    baz_doc = (app.srcdir / 'generated' / 'core' / 'baz.rst')
    assert baz_doc.exists()
    assert ('.. asdf-schema::\n'
            '    :schema_root: schemas\n'
            '\n'
            '    core/baz\n') in baz_doc.text()


@pytest.mark.sphinx('dummy', testroot='global-config')
def test_generation_global_config(app, status, warning):
    app.builder.build_all()

    foo_doc = (app.srcdir / 'generated' / 'foo.rst')
    assert foo_doc.exists()
    assert ('.. asdf-schema::\n'
            '    :schema_root: a/b/c/schemas\n'
            '\n'
            '    foo\n') in foo_doc.text()

    bar_doc = (app.srcdir / 'generated' / 'bar.rst')
    assert bar_doc.exists()
    assert ('.. asdf-schema::\n'
            '    :schema_root: a/b/c/schemas\n'
            '\n'
            '    bar\n') in bar_doc.text()

    baz_doc = (app.srcdir / 'generated' / 'core' / 'baz.rst')
    assert baz_doc.exists()
    assert ('.. asdf-schema::\n'
            '    :schema_root: a/b/c/schemas\n'
            '\n'
            '    core/baz\n') in baz_doc.text()


@pytest.mark.sphinx('dummy', testroot='global-prefix')
def test_generation_global_prefix(app, status, warning):
    app.builder.build_all()

    foo_doc = (app.srcdir / 'generated' / 'a' / 'b' / 'c' / 'foo.rst')
    assert foo_doc.exists()
    assert ('.. asdf-schema::\n'
            '    :standard_prefix: a/b/c\n'
            '    :schema_root: schemas\n'
            '\n'
            '    foo\n') in foo_doc.text()

    bar_doc = (app.srcdir / 'generated' / 'a' / 'b' / 'c' / 'bar.rst')
    assert bar_doc.exists()
    assert ('.. asdf-schema::\n'
            '    :standard_prefix: a/b/c\n'
            '    :schema_root: schemas\n'
            '\n'
            '    bar\n') in bar_doc.text()

    baz_doc = (app.srcdir / 'generated' / 'a' / 'b' / 'c' / 'core' / 'baz.rst')
    assert baz_doc.exists()
    assert ('.. asdf-schema::\n'
            '    :standard_prefix: a/b/c\n'
            '    :schema_root: schemas\n'
            '\n'
            '    core/baz\n') in baz_doc.text()


@pytest.mark.sphinx('dummy', testroot='basic-generation')
def test_basic_build(app, status, warning):
    app.builder.build_all()

    # Test each of the generated schema documents
    for name in ['foo', 'bar', 'core/baz']:
        doctree_path = app.doctreedir / 'generated' / '{}.doctree'.format(name)
        doc = pickle.loads(doctree_path.bytes())

        title = doc.traverse(nodes.title)[0]
        assert title.astext() == name

        schema_top = doc.traverse(sa_nodes.schema_doc)
        assert len(schema_top) > 0
