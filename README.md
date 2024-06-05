# qc-opendrive

This project implements the OpenDrive Python checker for the ASAM Quality Checker
framework.

In this project, several checks are implemented in order to guarantee the sanity
of OpenDrive (.xodr) files.

## Installation

To install the project, run:

```
pip install -r requirements.txt
```

This will install the needed dependencies to your local Python.

## Usage

The checker can be used as a Python script:

```
python src/main.py --help

usage: QC OpenDrive Checker [-h] (-d | -c CONFIG_PATH)

This is a collection of scripts for checking validity of OpenDrive (.xodr) files.

options:
  -h, --help            show this help message and exit
  -d, --default_config
  -c CONFIG_PATH, --config_path CONFIG_PATH

```

### Example

- No issues found

```
$ python python src/main.py \
    -c tests/data/road_lane_access_no_mix_of_deny_or_allow/configs/road_lane_access_no_mix_of_deny_or_allow_18_valid_config.xml
2024-06-05 18:29:23,551 - Initializing checks
2024-06-05 18:29:23,551 - Executing semantic checks
2024-06-05 18:29:23,552 - Executing road.lane.access.no_mix_of_deny_or_allow check
2024-06-05 18:29:23,552 - Issues found - 0
2024-06-05 18:29:23,552 - Done
```

- Issues found on file

```
python src/main.py -c tests/data/road_lane_access_no_mix_of_deny_or_allow/configs/road_lane_access_no_mix_of_deny_or_allow_18_invalid_config.xml
2024-06-05 18:29:53,950 - Initializing checks
2024-06-05 18:29:53,950 - Executing semantic checks
2024-06-05 18:29:53,951 - Executing road.lane.access.no_mix_of_deny_or_allow check
2024-06-05 18:29:53,951 - Issues found - 1
2024-06-05 18:29:53,951 - Done
```

The module will output the report to the defined `resultFile` in the
configuration. For the examples above, it would be `xodrBundleReport.xqar`.

## Tests

To run the tests, you need to have installed the main dependencies mentioned
at [Instalation](#installation).

Install Python tests and development dependencies:

```
pip install -r requirements-tests.txt
```

Execute tests:

```
pytest -vv
```

They should output something similar to:

```
===================== test session starts =====================
platform linux -- Python 3.11.9, pytest-8.2.2, pluggy-1.5.0 -- /home/tripel/asam/qc-opendrive/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/tripel/asam/qc-opendrive
configfile: pytest.ini
collected 4 items

tests/test_semantic_checks.py::test_road_lane_access_no_mix_of_deny_or_allow[17_invalid] PASSED                                                                                     [ 25%]
tests/test_semantic_checks.py::test_road_lane_access_no_mix_of_deny_or_allow[17_valid] PASSED                                                                                       [ 50%]
tests/test_semantic_checks.py::test_road_lane_access_no_mix_of_deny_or_allow[18_invalid] PASSED                                                                                     [ 75%]
tests/test_semantic_checks.py::test_road_lane_access_no_mix_of_deny_or_allow[18_valid] PASSED                                                                                       [100%]

===================== 4 passed in 0.24s =====================
```

You can check more options for pytest at its [own documentation](https://docs.pytest.org/).

## Contributing

For contributing, you need to install the development requirements besides the
test and installation requirements, for that run:

```
pip install -r requirements-dev.txt
```

You need to have pre-commit installed and install the hooks:

```
pre-commit install
```
