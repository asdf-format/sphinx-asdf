from docutils import nodes
from jinja2 import Environment


template_env = Environment()
headerlink_template = template_env.from_string("""
  <a class="headerlink" name="{{ name }}" href="#{{ name }}" title="{{ title }}">¶</a>
    """)


class schema_doc(nodes.compound):
    """Marker for the top level of the ASDF schema document"""

    def visit_html(self, node):
        pass

    def depart_html(self, node):
        pass


class schema_title(nodes.compound):

    def visit_html(self, node):
        self.body.append(r'<div class="schema_title">')

    def depart_html(self, node):
        self.body.append(r'</div>')


class toc_link(nodes.line):

    def visit_html(self, node):
        text = node[0].title()
        self.body.append('<a class="toc-link" href="#{}">'.format(text))

    def depart_html(self, node):
        self.body.append('</a>')


class schema_header_title(nodes.line):

    def visit_html(self, node):
        self.body.append('<h4>')

    def depart_html(self, node):
        self.body.append('</h4>')


class schema_description(nodes.compound):

    def visit_html(self, node):
        self.body.append(r'<div class="property_description"')

    def depart_html(self, node):
        self.body.append(r'</div>')


class section_header(nodes.line):

    def visit_html(self, node):
        self.body.append(r'<h3 class="section-header">')

    def depart_html(self, node):
        self.body.append(headerlink_template.render(name=node[0].title()))
        self.body.append(r'</h3>')


class schema_properties(nodes.compound):

    def visit_html(self, node):
        self.body.append(r'<div class="schema_properties" id="{}">'.format(node.get('id')))

    def depart_html(self, node):
        self.body.append(r'</div>')


class schema_property(nodes.compound):

    def visit_html(self, node):
        self.body.append(r'<li class="list-group-item" id="{}">'.format(node.get('id')))

    def depart_html(self, node):
        self.body.append(r'</li>')


class schema_property_name(nodes.line):

    def visit_html(self, node):
        self.body.append(r'<div class="schema_property_name">')

    def depart_html(self, node):
        self.body.append(r'</div>')


class schema_property_details(nodes.compound):

    def visit_html(self, node):
        self.body.append(r'<table><tr>')
        self.body.append('<td><b>')
        if node.get('ref', None) is not None:
            self.body.append('<a href={}>{}</a>'.format(node.get('ref'), node.get('typ')))
        else:
            self.body.append(node.get('typ'))
        self.body.append('</b></td>')
        if node.get('required'):
            self.body.append(r'<td><em>Required</em></td>')

    def depart_html(self, node):
        self.body.append(r'</tr></table>')


class asdf_tree(nodes.bullet_list):

    def visit_html(self, node):
        self.body.append(r'<ul class="list-group">')

    def depart_html(self, node):
        self.body.append(r'</ul>')


class asdf_ref(nodes.line):

    def visit_html(self, node):
        self.body.append('<a class="asdf_ref" href="{}">'.format(node.get('href')))

    def depart_html(self, node):
        self.body.append(r'</a>')


class example_section(nodes.compound):

    def visit_html(self, node):
        self.body.append('<div class="example-section">')

    def depart_html(self, node):
        self.body.append(r'</div>')


class example_item(nodes.compound):

    def visit_html(self, node):
        self.body.append(r'<div class="item example-item">')

    def depart_html(self, node):
        self.body.append(r'</div>')

class example_description(nodes.compound):

    def visit_html(self, node):
        self.body.append(r'<div class="example-description">')

    def depart_html(self, node):
        self.body.append(r'</div>')


class schema_combiner_body(nodes.compound):

    def visit_html(self, node):
        self.body.append("""
<button class="btn btn-primary" data-toggle="collapse" href="#{0}" aria-expanded="false">
    <span class="hidden">Hide </span>Details
</button>
<div class="collapse" id="{0}">
        """.format(node.get('path')))

    def depart_html(self, node):
        self.body.append('</div>')


class schema_combiner_list(nodes.bullet_list):

    def visit_html(self, node):
        self.body.append('<ul class="combiner-list">')

    def depart_html(self, node):
        self.body.append('</ul>')


class schema_combiner_item(nodes.list_item):

    def visit_html(self, node):
        self.body.append('<li class="combiner-list-item">')

    def depart_html(self, node):
        self.body.append('</li>')


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


__all__ = [klass.__name__ for klass in custom_nodes] + ['add_asdf_nodes']


def add_asdf_nodes(app):

    for node in custom_nodes:
        app.add_node(node, html=(node.visit_html, node.depart_html))
