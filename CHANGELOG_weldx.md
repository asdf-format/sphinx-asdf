# sphinx-weldx CHANGELOG

## changes form `sphinx-asdf` 
- don't import bootstrap theme into `schema.html` (breaks pydata theme navbar) [sphinx-asdf-issue](https://github.com/asdf-format/sphinx-asdf/issues/12)
- add parsing of `wx_unit` and `wx_shape`
- add `tag` parsing
- add `oneOf` to combiner parsing
- skip looking for ASDF directives for files in in `_autosummary` directory (should be a plugin option later)