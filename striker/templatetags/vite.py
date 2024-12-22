from pathlib import Path

import yaml
from django import template
from django.templatetags.static import StaticNode

register = template.Library()
vite_manifest = Path("static/vite/.vite/manifest.json").resolve()


def vite_manifest_data():
    return yaml.safe_load(vite_manifest.read_text())


@register.simple_tag()
def vite(file):
    data = vite_manifest_data().get(file)
    if not data or not data.get("isEntry"):
        raise Exception(f"No such entry point {file}")
    return StaticNode.handle_simple(data["file"])
