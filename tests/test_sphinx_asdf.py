import os

import pytest
from tempfile import gettempdir

from sphinx.testing.path import path


@pytest.fixture(scope='session')
def rootdir():
    return path(__file__).parent.abspath()


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
