# asam-qc-opendrive

This project implements the [ASAM OpenDrive Checker Bundle](checker_bundle_doc.md).

- [asam-qc-opendrive](#asam-qc-opendrive)
  - [Installation and usage](#installation-and-usage)
    - [Installation using pip](#installation-using-pip)
      - [To use as a library](#to-use-as-a-library)
      - [To use as an application](#to-use-as-an-application)
    - [Installation from source](#installation-from-source)
    - [Example output](#example-output)
  - [Register Checker Bundle to ASAM Quality Checker Framework](#register-checker-bundle-to-asam-quality-checker-framework)
    - [Linux Manifest Template](#linux-manifest-template)
  - [Tests](#tests)
    - [Execute tests](#execute-tests)
  - [Contributing](#contributing)

## Installation and usage

asam-qc-opendrive can be installed using pip or from source.

### Installation using pip

asam-qc-opendrive can be installed using pip, so that it can be used as a library or
as an application.

```bash
pip install asam-qc-opendrive@git+https://github.com/asam-ev/qc-opendrive@main
```

**Note**: To install from different sources, you can replace `@main` with
your desired target. For example, `develop` branch as `@develop`.

#### To use as a library

After installation, the usage is similar to the one expressed in the
[`main.py`](./qc_opendrive/main.py) script:

```Python3
from qc_opendrive.base import utils, models
```

#### To use as an application

```bash
qc_opendrive --help

usage: QC OpenDrive Checker [-h] (-d | -c CONFIG_PATH)

This is a collection of scripts for checking validity of OpenDrive (.xodr) files.

options:
  -h, --help            show this help message and exit
  -d, --default_config
  -c CONFIG_PATH, --config_path CONFIG_PATH

```

The following commands are equivalent:

```bash
qc_opendrive --help
python qc_opendrive/main.py --help
python -m qc_opendrive.main --help
```

### Installation from source

The project can be installed from source using [Poetry](https://python-poetry.org/).

```bash
poetry install
```

After installing from source, the usage are similar to above.

```bash
qc_opendrive --help
python qc_opendrive/main.py --help
python -m qc_opendrive.main --help
```

It is also possible to execute the qc_opendrive application using Poetry.

```bash
poetry run qc_opendrive --help

usage: QC OpenDrive Checker [-h] (-d | -c CONFIG_PATH)

This is a collection of scripts for checking validity of OpenDrive (.xodr) files.

options:
  -h, --help            show this help message and exit
  -d, --default_config
  -c CONFIG_PATH, --config_path CONFIG_PATH
```

### Example output

- No issues found

```bash
$ python qc_opendrive/main.py -c example_config/config.xml

2024-06-05 18:29:23,551 - Initializing checks
2024-06-05 18:29:23,551 - Executing semantic checks
2024-06-05 18:29:23,552 - Executing road.lane.access.no_mix_of_deny_or_allow check
2024-06-05 18:29:23,552 - Issues found - 0
2024-06-05 18:29:23,552 - Done
```

- Issues found

```bash
python qc_opendrive/main.py -c example_config/config.xml

2024-06-05 18:29:53,950 - Initializing checks
2024-06-05 18:29:53,950 - Executing semantic checks
2024-06-05 18:29:53,951 - Executing road.lane.access.no_mix_of_deny_or_allow check
2024-06-05 18:29:53,951 - Issues found - 1
2024-06-05 18:29:53,951 - Done
```

## Register Checker Bundle to ASAM Quality Checker Framework

Manifest file templates are provided in the [manifest_templates](manifest_templates/) folder to register the ASAM OpenDrive Checker Bundle with the [ASAM Quality Checker Framework](https://github.com/asam-ev/qc-framework/tree/main).

### Linux Manifest Template

To register this Checker Bundle in Linux, use the [linux_manifest.json](manifest_templates/linux_manifest.json) template file. Replace the path to the Python executable `/home/user/.venv/bin/python` in the `exec_command` with the path to the Python executable where the Checker Bundle is installed.

## Tests

To run the tests, you need to install the extra test dependency.

```bash
poetry install --with dev
```

### Execute tests


```bash
python -m pytest -vv
```

or

```bash
poetry run pytest -vv
```

They should output something similar to:

```bash
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
...
===================== 4 passed in 0.24s =====================
```

You can check more options for pytest at its [own documentation](https://docs.pytest.org/).

## Contributing

For contributing, you need to install the development requirements. For that run:

```bash
poetry install --with dev
```

You need to have pre-commit installed and install the hooks:

```
pre-commit install
```
