from docutils import nodes

headerlink_template = """
  <a class="headerlink" name="{name}" href="#{name}" title="{title}">¶</a>
    """


class schema_doc(nodes.compound):
    """Marker for the top level of the ASDF schema document"""

    def visit_html(self, node):
        pass

    def depart_html(self, node):
        pass


class schema_title(nodes.compound):
    def visit_html(self, node):
        self.body.append(r'<div class="schema-title">')

    def depart_html(self, node):
        self.body.append(r"</div>")


class toc_link(nodes.bullet_list):
    def visit_html(self, node):
        self.body.append(f'<li><a class="toc-link" href="#{node["text"]}">{node["text"]}')

    def depart_html(self, node):
        self.body.append("</a></li>")


class schema_header_title(nodes.line):
    def visit_html(self, node):
        self.body.append("<h4>")

    def depart_html(self, node):
        self.body.append("</h4>")


class schema_description(nodes.compound):
    def visit_html(self, node):
        self.body.append(r'<div class="property-description">')

    def depart_html(self, node):
        self.body.append(r"</div>")


class section_header(nodes.line):
    def visit_html(self, node):
        self.body.append(r"<h3>")

    def depart_html(self, node):
        self.body.append(headerlink_template.format(name=node[0].title(), title=""))
        self.body.append(r"</h3>")


class schema_properties(nodes.compound):
    def visit_html(self, node):
        self.body.append(r'<div class="schema-properties" id="{}">'.format(node.get("id")))

    def depart_html(self, node):
        self.body.append(r"</div>")


class schema_property(nodes.compound):
    def visit_html(self, node):
        self.body.append(r'<li class="schema-property" id="{}">'.format(node.get("id")))

    def depart_html(self, node):
        self.body.append(r"</li>")


class schema_property_name(nodes.line):
    def visit_html(self, node):
        self.body.append(r'<div class="schema-property-name"><h4>')

    def depart_html(self, node):
        self.body.append(r"</h4></div>")


class schema_property_details(nodes.compound):
    def visit_html(self, node):
        self.body.append(r"<table><tr>")
        self.body.append("<td><b>")
        if node.get("ref", None) is not None:
            self.body.append(f"<a href={node.get('ref')}>{node.get('typ')}</a>")
        else:
            self.body.append(node.get("typ"))
        self.body.append("</b></td>")
        if node.get("required"):
            self.body.append(r"<td><em>Required</em></td>")

    def depart_html(self, node):
        self.body.append(r"</tr></table>")


class asdf_tree(nodes.bullet_list):
    def visit_html(self, node):
        self.body.append(r'<ul class="asdf-tree">')

    def depart_html(self, node):
        self.body.append(r"</ul>")


class asdf_ref(nodes.line):
    def visit_html(self, node):
        self.body.append(f'<a class="asdf-ref" href="{node.get("href")}">')

    def depart_html(self, node):
        self.body.append(r"</a>")


class example_section(nodes.compound):
    def visit_html(self, node):
        self.body.append('<div class="example-section">')

    def depart_html(self, node):
        self.body.append(r"</div>")


class example_item(nodes.compound):
    def visit_html(self, node):
        self.body.append(r'<div class="example-item">')

    def depart_html(self, node):
        self.body.append(r"</div>")


class example_description(nodes.compound):
    def visit_html(self, node):
        self.body.append(r'<div class="example-description">')

    def depart_html(self, node):
        self.body.append(r"</div>")


class schema_combiner_body(nodes.compound):
    def visit_html(self, node):
        self.body.append(
            f"""
<div class="combiner-body" id="{node.get('path')}">
        """
        )

    def depart_html(self, node):
        self.body.append("</div>")


class schema_combiner_list(nodes.bullet_list):
    def visit_html(self, node):
        self.body.append('<ul class="combiner-list">')

    def depart_html(self, node):
        self.body.append("</ul>")


class schema_combiner_item(nodes.list_item):
    def visit_html(self, node):
        self.body.append('<li class="combiner-list-item">')

    def depart_html(self, node):
        self.body.append("</li>")


custom_nodes = [
    schema_doc,
    schema_title,
    toc_link,
    schema_header_title,
    schema_description,
    schema_properties,
    schema_property,
    schema_property_name,
    schema_property_details,
    schema_combiner_body,
    schema_combiner_list,
    schema_combiner_item,
    section_header,
    asdf_tree,
    asdf_ref,
    example_section,
    example_item,
    example_description,
]


__all__ = [klass.__name__ for klass in custom_nodes] + ["add_asdf_nodes"]


def add_asdf_nodes(app):
    for node in custom_nodes:
        app.add_node(node, html=(node.visit_html, node.depart_html))
