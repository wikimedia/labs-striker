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

import base64
import hashlib
import logging

import sshpubkeys

logger = logging.getLogger(__name__)


class SSHPublicKey(sshpubkeys.SSHKey):
    @property
    def type_name(self):
        if self.key_type == b"ssh-dss":
            return "DSA"
        elif self.key_type == b"ssh-rsa":
            return "RSA"
        elif self.key_type.startswith(b"ecdsa-sha"):
            return "ECDSA"
        elif self.key_type == b"ssh-ed25519":
            return "ED25519"
        else:
            return self.key_type.decode("utf-8")


def parse_ssh_key(pubkey):
    key = SSHPublicKey(pubkey, strict_mode=True, skip_option_parsing=True)
    try:
        key.parse()
    except sshpubkeys.InvalidKeyException as err:
        logger.exception('Failed to parse "%s"', err)
        key = None
    except NotImplementedError as err:
        logger.exception('Failed to parse "%s"', err)
        key = None
    return key


def invalid_key_hash(key):
    """Generate a hash for an invalid ssh public key."""
    return "INVALID:{}".format(
        base64.b85encode(hashlib.sha256(key.encode("utf-8")).digest()).decode("utf-8")
    )


def ssh_keys_by_hash(user):
    ret = {}
    for key in user.ldapuser.ssh_keys:
        pkey = parse_ssh_key(key)
        if pkey:
            ret[pkey.hash_sha256()] = key
        else:
            # T174112: handle invalid keys
            ret[invalid_key_hash(key)] = key
    return ret
