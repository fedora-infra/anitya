# -*- coding: utf-8 -*-

'''
Provide utility function to convert rst in docstring of functions into html
'''

import textwrap

import docutils
import docutils.examples
import markupsafe
import six


def modify_rst(rst):
    """ Downgrade some of our rst directives if docutils is too old. """

    # We catch Exception if we want :-p
    # pylint: disable=W0703
    try:
        # The rst features we need were introduced in this version
        minimum = [0, 9]
        version = [int(cpt) for cpt in docutils.__version__.split('.')]

        # If we're at or later than that version, no need to downgrade
        if version >= minimum:
            return rst
    except Exception:  # pragma: no cover
        # If there was some error parsing or comparing versions, run the
        # substitutions just to be safe.
        pass

    # On Fedora this will never work as the docutils version is to recent
    # Otherwise, make code-blocks into just literal blocks.
    substitutions = {  # pragma: no cover
        '.. code-block:: javascript': '::',
    }
    for old, new in substitutions.items():  # pragma: no cover
        rst = rst.replace(old, new)

    return rst  # pragma: no cover


def modify_html(html):
    """ Perform style substitutions where docutils doesn't do what we want.
    """

    substitutions = {
        '<tt class="docutils literal">': '<code>',
        '</tt>': '</code>',
    }
    for old, new in substitutions.items():
        html = html.replace(old, new)

    return html


def load_doc(endpoint):
    """ Utility to load an RST file and turn it into fancy HTML. """

    rst = six.text_type(textwrap.dedent(endpoint.__doc__))

    rst = modify_rst(rst)

    api_docs = docutils.examples.html_body(rst)

    api_docs = modify_html(api_docs)

    api_docs = markupsafe.Markup(api_docs)
    return api_docs
