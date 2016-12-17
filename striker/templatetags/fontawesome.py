# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Wikimedia Foundation and contributors.
# All Rights Reserved.
#
# This file is part of Striker.
#
# Striker is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Striker is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Striker.  If not, see <http://www.gnu.org/licenses/>.

from django import template
from django.utils import html

register = template.Library()


@register.simple_tag
def fa_icon(icon, *args, **kwargs):
    """Insert a FontAwesome icon.

    Add additional 'fa-*' styles as bare arguments:
        {% fa_icon "camera-retro" "lg" %}
        <i class="fa fa-camera-retro fa-lg"></i>

    Add additional attributes to using keyword args:
        {% fa_icon "home" title="Home" %}
        <i class="fa fa-home" title="Home"></i>

    Attributes with `-` in the name can be entered using `_` instead:
        {% fa_icon "square" aria_hidden="true" %}
        <i class="fa fa-square" aria-hidden="true"></i>
    """
    classes = ['fa', 'fa-%s' % icon]
    for arg in args:
        classes.append('fa-%s' % arg)
    attribs = ['class="%s"' % html.escape(' '.join(classes))]
    for name, value in kwargs.items():
        name = name.replace('_', '-')
        attribs.append('%s="%s"' % (html.escape(name), html.escape(value)))
    return html.mark_safe('<i %s></i>' % ' '.join(attribs))
