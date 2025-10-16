[Layout Template](templates/layout.html)
---
title: TradeNova
---

# Welcome to My Site

Here are all pages in the subfolder:

<ul>
{% for page in site.pages %}
  {% if page.path contains "templates" %}
    <li><a href="{{ page.url }}">{{ page.title | default: page.path }}</a></li>
  {% endif %}
{% endfor %}
</ul>
