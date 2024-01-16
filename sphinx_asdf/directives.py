import posixpath
from pprint import pformat

import yaml
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from sphinx import addnodes
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import nested_parse_with_titles

from .md2rst import md2rst
from .nodes import (
    asdf_ref,
    asdf_tree,
    example_description,
    example_item,
    example_section,
    schema_combiner_body,
    schema_combiner_item,
    schema_combiner_list,
    schema_description,
    schema_doc,
    schema_header_title,
    schema_properties,
    schema_property,
    schema_property_details,
    schema_property_name,
    schema_title,
    section_header,
    toc_link,
)

SCHEMA_DEF_SECTION_TITLE = "Schema Definitions"
EXAMPLE_SECTION_TITLE = "Examples"
INTERNAL_DEFINITIONS_SECTION_TITLE = "Internal Definitions"
ORIGINAL_SCHEMA_SECTION_TITLE = "Original Schema"


class schema_def(nodes.comment):
    def __init__(self, *args, **kwargs):
        self.schema_root = kwargs.pop("schema_root", "")
        self.standard_prefix = kwargs.pop("standard_prefix", "")
        super().__init__(*args, **kwargs)


class AsdfAutoschemas(SphinxDirective):
    required_arguments = 0
    optional_arguments = 2
    has_content = True
    option_spec = {
        "schema_root": directives.path,
        "standard_prefix": directives.unchanged,
    }

    def _process_asdf_toctree(self, standard_prefix):
        links = []
        for name in self.content:
            if not name:
                continue
            schema = self.env.path2doc(name.strip() + ".rst")
            link = posixpath.join("generated", standard_prefix, schema)
            links.append((schema, link))

        tocnode = addnodes.toctree()
        tocnode["includefiles"] = [x[1] for x in links]
        tocnode["entries"] = links
        tocnode["maxdepth"] = -1
        tocnode["glob"] = None

        return [tocnode]

    def run(self):
        standard_prefix = self.options.get("standard_prefix", self.env.config.asdf_schema_standard_prefix)

        # This is the case when we are actually using Sphinx to generate
        # documentation
        if not getattr(self.env, "autoasdf_generate", False):
            return self._process_asdf_toctree(standard_prefix)

        # This case allows us to use docutils to parse input documents during
        # the 'builder-inited' phase so that we can determine which new
        # document need to be created by 'autogenerate_schema_docs'. This seems
        # much cleaner than writing a custom parser to extract the schema
        # information.
        schema_root = self.options.get("schema_root", self.env.config.asdf_schema_path)
        return [
            schema_def(text=c.strip().split()[0], standard_prefix=standard_prefix, schema_root=schema_root)
            for c in self.content
        ]


class AsdfSchema(SphinxDirective):
    has_content = True
    optional_arguments = 2
    option_spec = {
        "schema_root": directives.path,
        "standard_prefix": directives.unchanged,
    }

    def run(self):
        self.envconfig = self.state.document.settings.env.config
        self.schema_name = self.content[0]
        schema_dir = self.options.get("schema_root", self.envconfig.asdf_schema_path)
        standard_prefix = self.options.get("standard_prefix", self.envconfig.asdf_schema_standard_prefix)
        srcdir = self.state.document.settings.env.srcdir

        schema_file = posixpath.join(srcdir, schema_dir, standard_prefix, self.schema_name) + ".yaml"

        with open(schema_file) as ff:
            raw_content = ff.read()
            schema = yaml.safe_load(raw_content)

        title = self._parse_title(schema.get("title", ""), schema_file)

        docnodes = schema_doc()
        docnodes.append(title)

        description = schema.get("description", "")
        if description:
            docnodes.append(schema_header_title(text="Description"))
            docnodes.append(self._parse_description(description, schema_file))

        docnodes.append(schema_header_title(text="Outline"))
        docnodes.append(self._create_toc(schema))

        docnodes.append(section_header(text=SCHEMA_DEF_SECTION_TITLE))
        docnodes.append(self._process_properties(schema, top=True))

        examples = schema.get("examples", [])
        if examples:
            docnodes.append(section_header(text=EXAMPLE_SECTION_TITLE))
            docnodes.append(self._process_examples(examples, schema_file))

        if "definitions" in schema:
            docnodes.append(section_header(text=INTERNAL_DEFINITIONS_SECTION_TITLE))
            for name in schema["definitions"]:
                path = f"definitions-{name}"
                tree = schema["definitions"][name]
                required = schema.get("required", [])
                docnodes.append(self._create_property_node(name, tree, name in required, path=path))

        docnodes.append(section_header(text=ORIGINAL_SCHEMA_SECTION_TITLE))
        docnodes.append(nodes.literal_block(text=raw_content, language="yaml"))

        return [docnodes]

    def _create_toc(self, schema):
        toc = nodes.bullet_list()
        toc.append(toc_link(text=SCHEMA_DEF_SECTION_TITLE))
        if "examples" in schema:
            toc.append(toc_link(text=EXAMPLE_SECTION_TITLE))
        if "definitions" in schema:
            toc.append(toc_link(text=INTERNAL_DEFINITIONS_SECTION_TITLE))
        toc.append(toc_link(text=ORIGINAL_SCHEMA_SECTION_TITLE))
        return toc

    def _markdown_to_nodes(self, text, filename):
        """
        This function is taken from the original schema conversion code written
        by Michael Droetboom.
        """
        rst = ViewList()
        for i, line in enumerate(md2rst(text).split("\n")):
            rst.append(line, filename, i + 1)

        node = nodes.section()
        node.document = self.state.document

        nested_parse_with_titles(self.state, rst, node)

        return node.children

    def _parse_title(self, title, filename):
        nodes = self._markdown_to_nodes(title, filename)
        return schema_title(None, *nodes)

    def _parse_description(self, description, filename):
        nodes = self._markdown_to_nodes(description, filename)
        return schema_description(None, *nodes)

    def _resolve_reference(self, schema_id):
        for mapping in self.envconfig.asdf_schema_reference_mappings:
            if schema_id.startswith(mapping[0]):
                relpath = posixpath.relpath(schema_id, mapping[0]).strip("/")
                if relpath == ".":
                    relpath = ""
                schema_id = posixpath.join(mapping[1], relpath).strip("/")
                break

        if not schema_id.endswith(".html"):
            schema_id += ".html"

        return schema_id

    def _create_reference(self, refname, shorten=False):
        if "#" in refname:
            schema_id, fragment = refname.split("#")
        else:
            schema_id = refname
            fragment = ""

        if schema_id:
            schema_id = self._resolve_reference(schema_id)
        if fragment:
            components = fragment.split("/")
            fragment = f"#{'-'.join(components[1:])}"
            if shorten and not schema_id:
                refname = components[-1]
        elif shorten:
            # TODO this should probably be:
            #   refname = schema_id
            # as it was previously
            #   rename = schema_id
            # and ruff cleaned this up as unused. However, changing it
            # to refname breaks some downstream packages
            pass

        return refname, schema_id + fragment

    def _create_ref_node(self, ref):
        treenodes = asdf_tree()
        refname, href = self._create_reference(ref)
        treenodes.append(asdf_ref(text=refname, href=href))
        return treenodes

    def _create_enum_node(self, enum_values):
        enum_nodes = nodes.compound()
        enum_nodes.append(nodes.paragraph(text="Only the following values are valid for this node:"))
        markdown = "\n".join([f"* **{val}**" for val in enum_values])
        enum_nodes.extend(self._markdown_to_nodes(markdown, ""))
        return enum_nodes

    def _create_array_items_node(self, items, path):
        path = self._append_to_path(path, "items")
        for combiner in ["anyOf", "allOf", "oneOf"]:
            if combiner in items:
                return self._create_combiner(items, combiner, array=True, path=path)

        node_list = nodes.compound()
        if isinstance(items, list):
            text = "The first {} item{} in the list must be the following types:"
            node_list.append(nodes.paragraph(text=text.format(len(items), "s" if len(items) > 1 else "")))
            item_list = nodes.bullet_list()
            for i, it in enumerate(items):
                item_path = self._append_to_path(path, i)
                item_list.append(self._process_properties(it, top=True, path=item_path))
            node_list.append(item_list)
        else:
            node_list.append(nodes.paragraph(text="Items in the array are restricted to the following types:"))
            node_list.append(self._process_properties(items, top=True, path=path))
        return node_list

    def _process_validation_keywords(self, schema, typename=None, path=""):
        node_list = []
        typename = typename or schema["type"]

        if typename == "string":
            if not ("minLength" in schema or "maxLength" in schema):
                node_list.append(nodes.emphasis(text="No length restriction"))
            if schema.get("minLength", 0):
                text = f"Minimum length: {schema['minLength']}"
                node_list.append(nodes.paragraph(text=text))
            if "maxLength" in schema:
                text = f"Maximum length: {schema['maxLength']}"
                node_list.append(nodes.paragraph(text=text))
            if "pattern" in schema:
                node_list.append(nodes.paragraph(text="Must match the following pattern:"))
                node_list.append(nodes.literal_block(text=schema["pattern"], language="none"))

        elif typename == "array":
            if schema.get("minItems", 0):
                text = f"Minimum length: {schema['minItems']}"
                node_list.append(nodes.paragraph(text=text))
            if "maxItems" in schema:
                text = f"Maximum length: {schema['maxItems']}"
                node_list.append(nodes.paragraph(text=text))
            if "additionalItems" in schema and "items" in schema:
                if isinstance(schema["items"], list) and schema["additionalItems"] is False:
                    node_list.append(nodes.emphasis(text="Additional items not permitted"))
            elif not ("minItems" in schema or "maxItems" in schema):
                node_list.append(nodes.emphasis(text="No length restriction"))

            if "items" in schema:
                node_list.append(self._create_array_items_node(schema["items"], path=path))

        # TODO: more numerical validation keywords
        elif typename in ["integer", "number"]:
            if "minimum" in schema:
                text = f"Minimum value: {schema['minimum']}"
                node_list.append(nodes.paragraph(text=text))
            if "maximum" in schema:
                text = f"Maximum value: {schema['maximum']}"
                node_list.append(nodes.paragraph(text=text))

        if "enum" in schema:
            node_list.append(self._create_enum_node(schema["enum"]))

        if "default" in schema:
            if typename in ["string", "integer", "number"]:
                if typename == "string" and not schema["default"]:
                    default = "''"
                else:
                    default = schema["default"]
                text = f"Default value: {default}"
                node_list.append(nodes.paragraph(text=text))
            else:
                default_node = nodes.compound()
                default_node.append(nodes.paragraph(text="Default value:"))
                default_node.append(nodes.literal_block(text=pformat(schema["default"]), language="none"))
                node_list.append(default_node)

        return node_list

    def _process_top_type(self, schema, path=""):
        tree = nodes.compound()
        prop = nodes.compound()
        typename = schema["type"]
        prop.append(schema_property_name(text=typename))
        prop.extend(self._process_validation_keywords(schema, path=path))
        tree.append(prop)
        return tree

    def _append_to_path(self, path, new):
        if not path:
            return str(new).lower()
        else:
            return f"{path}-{new}".lower()

    def _process_properties(self, schema, top=False, path=""):
        for combiner in ["anyOf", "allOf", "oneOf"]:
            if combiner in schema:
                return self._create_combiner(schema, combiner, top=top, path=path)

        if "properties" in schema:
            treenodes = asdf_tree()
            required = schema.get("required", [])
            for key, node in schema["properties"].items():
                new_path = self._append_to_path(path, key)
                treenodes.append(self._create_property_node(key, node, key in required, path=new_path))
            comment = nodes.paragraph(text="This type is an object with the following properties:")
            return schema_properties(None, *[comment, treenodes], id=path)
        elif "type" in schema:
            details = self._process_top_type(schema, path=path)
            return schema_properties(None, details, id=path)
        elif "$ref" in schema:
            ref = self._create_ref_node(schema["$ref"])
            return schema_properties(None, *[ref], id=path)
        elif "tag" in schema:
            ref = self._create_ref_node(schema["tag"])
            return schema_properties(None, *[ref], id=path)
        else:
            text = nodes.emphasis(text="This node has no type definition (unrestricted)")
            return schema_properties(None, text, id=path)

    def _create_combiner(self, items, combiner, array=False, top=False, path=""):
        if top or array:
            container_node = nodes.compound()
        else:
            combiner_path = self._append_to_path(path, "combiner")
            container_node = schema_combiner_body(path=combiner_path)

        path = self._append_to_path(path, combiner)

        if array:
            text = "Items in the array must be **{}** of the following types:"
        else:
            text = "This node must validate against **{}** of the following:"
        text = text.format(combiner.replace("Of", ""))
        text_nodes = self._markdown_to_nodes(text, "")
        container_node.extend(text_nodes)

        combiner_list = schema_combiner_list()
        for i, tree in enumerate(items[combiner]):
            new_path = self._append_to_path(path, i)
            properties = self._process_properties(tree, path=new_path)
            combiner_list.append(schema_combiner_item(None, *[properties]))

        container_node.append(combiner_list)
        container_node["ids"] = [path]
        return schema_properties(None, *[container_node], id=path)

    def _create_property_node(self, name, tree, required, path=""):
        description = tree.get("description", "")

        if "$ref" in tree:
            typ, ref = self._create_reference(tree.get("$ref"), shorten=True)
        elif "tag" in tree:
            _tag = tree.get("tag")
            typ, ref = self._create_reference(_tag, shorten=True)
            if "*" in _tag:
                ref = None
        else:
            typ = tree.get("type", "object")
            ref = None

        prop = schema_property(id=path)
        prop.append(schema_property_name(text=name))
        prop.append(schema_property_details(typ=typ, required=required, ref=ref))
        prop.append(self._parse_description(description, ""))
        if typ != "object":
            prop.extend(self._process_validation_keywords(tree, typename=typ, path=path))
        else:
            prop.append(self._process_properties(tree, path=path))

        prop["ids"] = [path]
        return prop

    def _process_examples(self, tree, filename):
        examples = example_section(num=len(tree))
        for i, example in enumerate(tree):
            node = example_item()
            desc_text = self._markdown_to_nodes(example[0] + ":", filename)
            description = example_description(None, *desc_text)
            node.append(description)
            node.append(nodes.literal_block(text=example[1], language="yaml"))
            examples.append(node)
        return examples
