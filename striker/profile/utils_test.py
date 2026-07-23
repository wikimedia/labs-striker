# -*- coding: utf-8 -*-
#
# Copyright (c) 2026 Wikimedia Foundation and contributors.
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

import pytest

from .utils import SSHPublicKey, parse_ssh_key


@pytest.mark.parametrize(
    "key",
    (
        "",
        "blah blah",
        "ssh-ed25519",
        "ssh-ed25519 123456fake",
        """---- BEGIN SSH2 PUBLIC KEY ----
Comment: "256-bit ED25519, converted by taavi@runko from OpenSSH"
AAAAC3NzaC1lZDI1NTE5AAAAIJ4dGYmWjhI4PuL5jLFphBkvK1hQkH9y2ujn2MTP9tbE
---- END SSH2 PUBLIC KEY ----
""",
    ),
)
def test_parse_ssh_key_invalid(key):
    assert parse_ssh_key(key) is None


def test_parse_ssh_key_valid():
    key = parse_ssh_key(
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJ4dGYmWjhI4PuL5jLFphBkvK1hQkH9y2ujn2MTP9tbE taavi@runko"
    )
    assert isinstance(key, SSHPublicKey)
    assert key.type_name == "ED25519"
    assert key.comment == "taavi@runko"
    assert key.hash_sha256() == "SHA256:6bC96q+FhXJM8V7eADtfD8SZaebwYSK82IgWvnmuths"
