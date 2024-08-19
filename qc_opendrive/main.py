import argparse
import logging

from qc_baselib import Configuration, Result
from qc_baselib.models.common import ParamType

from qc_opendrive import constants
from qc_opendrive.checks.semantic import semantic_checker
from qc_opendrive.checks.geometry import geometry_checker
from qc_opendrive.checks.performance import performance_checker

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


def args_entrypoint() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="QC OpenDrive Checker",
        description="This is a collection of scripts for checking validity of OpenDrive (.xodr) files.",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--default_config", action="store_true")
    group.add_argument("-c", "--config_path")

    parser.add_argument("-g", "--generate_markdown", action="store_true")

    return parser.parse_args()


def main():
    args = args_entrypoint()

    logging.info("Initializing checks")

    if args.default_config:
        raise RuntimeError("Not implemented.")
    else:
        config = Configuration()
        config.load_from_file(xml_file_path=args.config_path)

        result = Result()
        result.register_checker_bundle(
            name=constants.BUNDLE_NAME,
            build_date="2024-06-05",
            description="OpenDrive checker bundle",
            version=constants.BUNDLE_VERSION,
            summary="",
        )
        result.set_result_version(version=constants.BUNDLE_VERSION)

        input_file_path = config.get_config_param("InputFile")
        input_param = ParamType(name="InputFile", value=input_file_path)
        result.get_checker_bundle_result(constants.BUNDLE_NAME).params.append(
            input_param
        )

        semantic_checker.run_checks(config=config, result=result)
        geometry_checker.run_checks(config=config, result=result)
        performance_checker.run_checks(config=config, result=result)

        result.write_to_file(
            config.get_checker_bundle_param(
                checker_bundle_name=constants.BUNDLE_NAME, param_name="resultFile"
            )
        )

        if args.generate_markdown:
            result.write_markdown_doc("generated_checker_bundle_doc.md")

    logging.info("Done")


if __name__ == "__main__":
    main()
