# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re
from typing import List, Optional
from semver.version import Version


def _is_lower_bound(expression: str) -> bool:
    pattern = r"^(>=|>)"
    match = re.match(pattern, expression)
    if match:
        return True
    else:
        return False


def _get_version_clause(applicable_version: str) -> bool:
    version_clauses = applicable_version.split(",")
    version_clauses = [clause.replace(" ", "") for clause in version_clauses]
    return version_clauses


def is_valid_version_expression(version_expression: str) -> bool:
    version_clauses = _get_version_clause(version_expression)
    pattern = r"^(>=|<=|>|<)(\d+)\.(\d+)\.(\d+)$"
    for clause in version_clauses:
        match = re.match(pattern, clause)
        if not match:
            return False

    return True


def has_lower_bound(applicable_version: str) -> bool:
    """
    Check if there is at least one lower bound in an applicable version string.
    Example:
        "<1.0.0,>0.0.1" returns True
        "<1.0.0" returns False
    """
    expressions = applicable_version.split(",")

    for expr in expressions:
        if _is_lower_bound(expr):
            return True

    return False


def match(version: str, applicable_version: str) -> bool:
    """
    Check if the version is valid, given an applicable version.

    Applicable version is comma separated. The comma acts as a logical AND.
    A candidate version must match all given version clauses in order to match
    the applicable_version as a whole.

    The validity check follows the concept of Python version specifiers.
    See: https://packaging.python.org/en/latest/specifications/version-specifiers/#id5

    :param version: The version to be checked.
    :param applicable_version: Comma separated applicable version.
    """
    version_clauses = _get_version_clause(applicable_version)

    parsed_version = Version.parse(version)

    for clause in version_clauses:
        is_matched = parsed_version.match(clause)
        if not is_matched:
            return False

    return True
