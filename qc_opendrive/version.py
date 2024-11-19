# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re
from typing import List
from semver.version import Version


_is_lower_bound_pattern = re.compile(r"^>")


def _is_lower_bound(expression: str) -> bool:
    return bool(_is_lower_bound_pattern.match(expression))


_re_split_clauses = re.compile(r"\s*,\s*")
_re_remove_spaces = re.compile(r"\s+")


def _get_version_clauses(applicable_versions: str) -> List[str]:
    version_clauses = _re_split_clauses.split(applicable_versions)
    version_clauses = [_re_remove_spaces.sub("", vc) for vc in version_clauses]
    return [vc for vc in version_clauses if vc != ""]


_re_is_valid_clause = re.compile(r"^([<>]=?)(\d+)\.(\d+)\.(\d+)$")


def _is_valid_clause(clause: str) -> bool:
    return bool(_re_is_valid_clause.match(clause))


def is_valid_version_expression(version_expression: str) -> bool:
    return all(
        _is_valid_clause(clause) for clause in _get_version_clauses(version_expression)
    )


def has_lower_bound(applicable_versions: str) -> bool:
    """
    Check if there is at least one lower bound in an applicable version string.
    Example:
        "<1.0.0,>0.0.1" returns True
        "<1.0.0" returns False
    """
    return any(
        (
            _is_lower_bound(clause)
            for clause in _get_version_clauses(applicable_versions)
        )
    )


def match(version: str, applicable_versions: str) -> bool:
    """
    Check if the version is valid, given an applicable version.
    Applicable version is comma separated. The comma acts as a logical AND.
    A candidate version must match all given version clauses in order to match
    the applicable_version as a whole.
    The validity check follows the concept of Python version specifiers.
    See: https://packaging.python.org/en/latest/specifications/version-specifiers/#id5

    :param version: The version to be checked.
    :param applicable_version: Comma separated applicable version. Invalid version clauses will force the check to fail
    :return: a boolean for the match
    """
    version = Version.parse(version)
    clauses = _get_version_clauses(applicable_versions)

    return all(_is_valid_clause(clause) and version.match(clause) for clause in clauses)
