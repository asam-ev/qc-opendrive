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
    - [Windows Manifest Template](#windows-manifest-template)
    - [Example Configuration File](#example-configuration-file)
  - [Tests](#tests)
    - [Execute tests](#execute-tests)
  - [Contributing](#contributing)

## Installation and usage

asam-qc-opendrive can be installed using pip or from source.

### Installation using pip

asam-qc-opendrive can be installed using pip, so that it can be used as a library or
as an application.

**From PyPi**

```bash
pip install asam-qc-opendrive
```

**From GitHub repository**

```bash
pip install asam-qc-opendrive@git+https://github.com/asam-ev/qc-opendrive@main
```

The above command will install `asam-qc-opendrive` from the `main` branch. If you want to install `asam-qc-opendrive` from another branch or tag, replace `@main` with the desired branch or tag.

**From a local repository**

```bash
pip install /home/user/qc-opendrive
```

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

To register this Checker Bundle in Linux, use the [linux_xodr_manifest.json](manifest_templates/linux_xodr_manifest.json) template file.

If the asam-qc-opendrive is installed in a virtual environment, the `exec_command` needs to be adjusted as follows:

```json
"exec_command": "source <venv>/bin/activate && cd $ASAM_QC_FRAMEWORK_WORKING_DIR && qc_opendrive -c $ASAM_QC_FRAMEWORK_CONFIG_FILE"
```

Replace `<venv>/bin/activate` by the path to your virtual environment.

### Windows Manifest Template

To register this Checker Bundle in Windows, use the [windows_xodr_manifest.json](manifest_templates/windows_xodr_manifest.json) template file.

If the asam-qc-opendrive is installed in a virtual environment, the `exec_command` needs to be adjusted as follows:

```json
"exec_command": "C:\\> <venv>\\Scripts\\activate.bat && cd %ASAM_QC_FRAMEWORK_WORKING_DIR% && qc_opendrive -c %ASAM_QC_FRAMEWORK_CONFIG_FILE%"
```

Replace `C:\\> <venv>\\Scripts\\activate.bat` by the path to your virtual environment.

### Example Configuration File

An example configuration file for using this Checker Bundle within the ASAM Quality Checker Framework is as follows.

```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<Config>

    <Param name="InputFile" value="test.xodr" />

    <CheckerBundle application="xodrBundle">
        <Param name="resultFile" value="xodr_bundle_report.xqar" />
        <Checker checkerId="check_asam_xodr_xml_valid_xml_document" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_xml_root_tag_is_opendrive" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_xml_fileheader_is_present" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_xml_version_is_defined" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_xml_valid_schema" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_road_lane_level_true_one_side" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_road_lane_access_no_mix_of_deny_or_allow" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_road_lane_link_lanes_across_lane_sections" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_road_linkage_is_junction_needed" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_road_lane_link_zero_width_at_start" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_road_lane_link_zero_width_at_end" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_road_lane_link_new_lane_appear" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_junctions_connection_connect_road_no_incoming_road" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_junctions_connection_one_connection_element" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_junctions_connection_one_link_to_incoming" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_junctions_connection_start_along_linkage" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_junctions_connection_end_opposite_linkage" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_road_geometry_parampoly3_length_match" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_road_lane_border_overlap_with_inner_lanes" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_road_geometry_parampoly3_arclength_range" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_road_geometry_parampoly3_normalized_range" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_performance_avoid_redundant_info" maxLevel="1" minLevel="3" />
        <Checker checkerId="check_asam_xodr_lane_smoothness_contact_point_no_horizontal_gaps" maxLevel="1" minLevel="3" />
    </CheckerBundle>

    <ReportModule application="TextReport">
        <Param name="strInputFile" value="Result.xqar" />
        <Param name="strReportFile" value="Report.txt" />
    </ReportModule>

</Config>
```

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

**Valid and invalid example OpenDrive files for future rules**

[This folder](tests/data/not_implemented_yet/) contains the valid and invalid sample OpenDrive files of the
rules that need to be implemented in the future. It can be used as a reference for anyone who
wants to contribute to the implementation of the rules.

Contributions of valid and invalid OpenDrive sample files are also welcome. New sample files can be added to [the same folder](tests/data/not_implemented_yet/).

**To implement a new checker**

1. Create a new Python module for each checker.
2. Specify the following global variables for the Python module

| Variable | Presence | Meaning |
| --- | --- | --- |
| `CHECKER_ID` | Required | The ID of the checker |
| `CHECKER_DESCRIPTION` | Required | The description of the checker |
| `CHECKER_PRECONDITIONS` | Required | A set of other checkers in which if any of them raise an issue, the current checker will be skipped |
| `RULE_UID` | Required | The rule UID of the rule that the checker will check |
| `APPLICABLE_VERSIONS` | Optional | An optional variable to define extra constraints on the applicable version. See details below. |

1. Implement the checker logic in the following function:

```python
def check_rule(checker_data: models.CheckerData) -> None:
    pass
```

4. Register the checker module in the following function in [main.py](qc_opendrive/main.py).

```python
def run_checks(config: Configuration, result: Result) -> None:
    ...
    # Add the following line to register your checker module
    execute_checker(your_checker_module, checker_data)
    ...
```

All the checkers in this checker bundle are implemented in this way. Take a look at some of them before implementing your first checker.

**A note on `APPLICABLE_VERSIONS`**

The `APPLICABLE_VERSIONS` variable can be used to define additional constraints on the versions of the input files that a rule supports, in addition to the **definition setting** in the rule UID. It can be specified in the same way as the [Python Version Specifiers](https://packaging.python.org/en/latest/specifications/version-specifiers/#id5). For example:

```python
APPLICABLE_VERSIONS = "<1.8.0"
APPLICABLE_VERSIONS = ">=1.6.0"
APPLICABLE_VERSIONS = "<1.8.0,>=1.6.0"
```

The specification consists of a series of version clauses, separated by commas. The comma is equivalent to a logical "AND" operator: a candidate version must match all given version clauses in order to match the **applicable versions** as a whole.

The **applicable versions** only supports versions of in the full semantic form `major.minor.patch`. Elision of `minor` or `patch` elements are not supported. For example, `1.7.0rc1` and `1.7` are not supported, but `1.7.0` is supported.

The **applicable versions** only supports the following comparison operators.

* `<` smaller than **(upper bound)**
* `<=` smaller or equal than **(upper bound)**
* `>` greater than **(lower bound)**
* `>=` greater or equal than **(lower bound)**

The **definition setting** in rule UID and the **applicable versions** together define the versions of the input file in which a rule can be applied. For example, let's consider a rule UID for ASAM OpenDRIVE `asam.net:xodr:1.6.0:*`. The **definition setting** in this case is `1.6.0`.

1. If no **applicable versions** is specified, a rule will be applied starting from the **definition setting** version, up to the most recent one.
    * For the example, if the `APPLICABLE_VERSIONS` variable does not exist, then the rule is applied to OpenDRIVE versions 1.6.0, 1.6.1, 1.7.0, 1.8.0: the internal representation of the version specifier is `>=1.6.0`.

2. If the **applicable versions** is specified, and defines only **upper bounds**, then the **definition setting** defines the lower bound
    * For the example, if `APPLICABLE_VERSIONS = "<1.8.0"`, then the rule is applied to OpenDRIVE versions 1.6.0, 1.6.1, 1.7.0: the internal representation of the version specifier is `>=1.6.0,<1.8.0`.

3. If the **applicable versions** is specified, and defines at least one **lower bound**, then the **definition setting** is ignored. Only the **lower bounds** defined in the **applicable versions** are taken into account.
    * For the example, if `APPLICABLE_VERSIONS = ">=1.5.0"`, then the rule is applied to OpenDRIVE versions 1.5.0, 1.6.0, 1.6.1, 1.7.0, 1.8.0: the internal representation of the version specifier is `>=1.5.0`.

| Case Number | Example Rule            | `APPLICABLE_VERSIONS` | Internal Representation          | File versions to be checked       |
|-------------|-------------------------|----------------------|----------------------------------|-----------------------------------|
| 1           | `asam.net:xodr:1.6.0:*` | `""`                 | `">=1.6.0"`                      | 1.6.0, 1.6.1, 1.7.0, 1.8.0        |
| 2           | `asam.net:xodr:1.6.0:*` | `"<1.8.0"`             | `">=1.6.0,<1.8.0"`           | 1.6.0, 1.6.1, 1.7.0               |
| 3           | `asam.net:xodr:1.6.0:*` | `">=1.5.0"`            | `">=1.5.0"` | 1.5.0, 1.6.0, 1.6.1, 1.7.0, 1.8.0 |
