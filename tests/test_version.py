# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from qc_opendrive import version as qc_version


@pytest.mark.parametrize(
    "applicable_version,has_lower_bound",
    [
        (">1.0.0", True),
        (">1.0.0,<2.0.0", True),
        (">1.0.0,<=2.0.0", True),
        (">=1.0.0", True),
        (">=1.0.0,<2.0.0", True),
        (">=1.0.0,<=2.0.0", True),
        (">=1.0.0,>=1.0.1,<=2.0.0", True),
        (">=1.0.0,<=1.0.1,<=2.0.0", True),
        ("<=2.0.0", False),
        ("<2.0.0", False),
        ("<=2.0.0,<=3.0.0", False),
        ("<2.0.0,<3.0.0", False),
        ("", False),
    ],
)
def test_has_lower_bound(applicable_version: str, has_lower_bound: bool) -> None:
    assert qc_version.has_lower_bound(applicable_version) == has_lower_bound


@pytest.mark.parametrize(
    "version,applicable_version,match",
    [
        ("1.7.0", ">=1.7.0", True),
        ("1.7.0", "<=1.7.0", True),
        ("1.7.0", ">1.7.0", False),
        ("1.7.0", "<1.7.0", False),
        ("1.7.0", "<1.7.0,<1.8.0", False),
        ("1.7.0", ">1.7.0,>1.6.0", False),
        ("1.7.0", ">=1.7.0,>1.6.0", True),
        ("1.7.0", ">=1.7.0,>1.8.0", False),
        ("1.7.0", "<=1.7.0,>1.8.0", False),
        ("1.7.0", "<=1.7.0,<1.8.0", True),
        ("1.7.0", "<=1.7.0,<1.6.0", False),
        ("1.7.0", "<=1.7.0,<1.8", False),
    ],
)
def test_match(version: str, applicable_version: str, match: bool) -> None:
    assert qc_version.match(version, applicable_version) == match


@pytest.mark.parametrize(
    "version_expression,is_valid",
    [
        ("1.7.0", False),
        (">1.7.0", True),
        (">=1.7.0", True),
        ("<1.7.0", True),
        ("<=1.7.0", True),
        ("==1.7.0", False),
        ("!=1.7.0", False),
        ("<1.7", False),
    ],
)
def test_is_valid_version_expression(version_expression: str, is_valid: bool) -> None:
    assert qc_version.is_valid_version_expression(version_expression) == is_valid
