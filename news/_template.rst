{% macro issue_url(value) -%}
   {%- if value.startswith("PR") -%}
     `PR#{{ value[2:] }} <https://github.com/fedora-infra/fedora-messaging/pull/{{ value[2:] }}>`_
   {%- elif value.startswith("C") -%}
     `{{ value[1:] }} <https://github.com/fedora-infra/fedora-messaging/commit/{{ value[1:] }}>`_
   {%- else -%}
     `#{{ value }} <https://github.com/fedora-infra/fedora-messaging/issues/{{ value }}>`_
   {%- endif -%}
{%- endmacro -%}

{% for section, _ in sections.items() %}
{% set underline = underlines[0] %}{% if section %}{{section}}
{{ underline * section|length }}{% set underline = underlines[1] %}

{% endif %}

{% if sections[section] %}
{% for category, val in definitions.items() if category in sections[section] and category != "author" %}
{{ definitions[category]['name'] }}
{{ underline * definitions[category]['name']|length }}

{% if definitions[category]['showcontent'] %}
{% for text, values in sections[section][category].items() %}
* {{ text }}
  ({% for value in values -%}
      {{ issue_url(value) }}
      {%- if not loop.last %}, {% endif -%}
   {%- endfor %})

{% endfor %}
{% else %}
* {{ sections[section][category]['']|sort|join(', ') }}

{% endif %}
{% if sections[section][category]|length == 0 %}
No significant changes.

{% else %}
{% endif %}

{% endfor %}
{% if sections[section]["author"] %}
{{definitions['author']["name"]}}
{{ underline * definitions['author']['name']|length }}
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

{% for text, values in sections[section]["author"].items() %}
* {{ text }}
{% endfor %}
{% endif %}

{% else %}
No significant changes.


{% endif %}
{% endfor %}
