from xodr.checks.schema_checks.schema.schema_files import SCHEMA_FILES
from result_report import IssueLevel, create_location_from_error, create_location_from_element, get_IssueLevel_from_str
from checker_data import CheckerData 
from pathlib import Path
from lxml import etree


import logging


def check_schema(checker_data: CheckerData) -> bool:
    logging.info(get_checker_id())
    
    abort_if_error = checker_data.config['abort_if_error']
    major, minor = checker_data.version
    
    format_name = checker_data.format_settings['name']
    schema_file = SCHEMA_FILES[f'{major}.{minor}'][0]
    schema_location = Path(__file__).parent / 'schema' / schema_file
    if schema_location.exists():
        try:
            schema = etree.XMLSchema(etree.parse(schema_location))
            result = schema.validate(checker_data.data)
            if not result:
                for error in schema.error_log:
                    issue_level = get_IssueLevel_from_str(error.level_name)
                    checker_data.checker.gen_issue(issue_level, error.message, create_location_from_error(error))
                    if issue_level == IssueLevel.ERROR and abort_if_error:
                        logging.error(f'Schema has critical error - abort!')
                        return False
        except:
            logging.exception(f'Cannot validate schema with {format_name} {major}.{minor}')
            checker_data.checker.gen_issue(IssueLevel.ERROR, f'Cannot check {format_name} schema.')
    else:
        logging.exception(f'Cannot find matching schema location for {format_name} version {major}.{minor} in {schema_location}')
        checker_data.checker.gen_issue(IssueLevel.ERROR, f'Cannot check {format_name} schema.')

    return True

def get_checker_id():
    return 'check schema'


def get_description():
    return f'check schema in OpenDRIVE file.'


def check(checker_data: CheckerData) -> bool:
    return check_schema(checker_data)
