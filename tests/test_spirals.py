# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
import pytest
from qc_opendrive.base.spiral import spiral_ode, spiral_fresnel

dataset_file = "tests/data/utils/spiral_values.json"
with open(dataset_file) as fp:
    dataset = json.load(fp)

@pytest.mark.parametrize("spiral", [spiral_fresnel, spiral_ode])
@pytest.mark.parametrize("data", dataset)
@pytest.mark.parametrize("direction", [(0, "X"), (1, "Y"), (2, "THETA")])
def test_spiral_ode(spiral, data, direction):
    output, label = direction
    
    params = data["params"]
    tests = data["tests"]
    for test in tests:
        out_ = test["out"]
        out = spiral(test["s"], *params)
        
        z, z_ = out[output], out_[output]
        assert z == pytest.approx(z_, abs=1e-6), \
            f"{label} {spiral.__name__}({test['s']}) = {z} != {z_} ({z - z_})" \
            f" sigma = {params[4] - params[3] / params[5]}), L = {params[5]}"
        


