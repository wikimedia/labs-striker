#!/usr/bin/env python3
"""Expand jinja2 templates."""
import argparse
import os
import sys

import jinja2


def kvpair(value):
    """Split key=value values."""
    return value.split("=")


def parse_args():
    """Read cli args."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--set",
        action="append",
        type=kvpair,
        default=[],
    )
    parser.add_argument(
        "-o", "--output",
        type=argparse.FileType('w'),
        default=sys.stdout,
    )
    parser.add_argument(
        "template",
        type=argparse.FileType('r'),
        default=sys.stdin,
    )
    return parser.parse_args()


def main():
    """Expand a template."""
    args = parse_args()
    ctx = dict(args.set)
    template = jinja2.Template(args.template.read())
    args.output.write(template.render(environ=os.environ, **ctx))


if __name__ == "__main__":
    main()
