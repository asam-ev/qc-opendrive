from xodr.checks.schema_checks.schema.schema_files import SCHEMA_FILES
from result_report import IssueLevel, FileLocation, create_location_from_element
from checker_data import CheckerData 

import logging


def check_version(checker_data: CheckerData) -> bool:
    logging.info(get_checker_id())
    
    major, minor = None, None
    format_name = checker_data.format_settings['name']

    try:
        header = checker_data.data.find('.//header')
        if header is None:
            checker_data.checker.gen_issue(IssueLevel.ERROR,
                                    f'Cannot determine {format_name} version. Could not find <header> in file.', FileLocation(checker_data.file))
            return False
        else:
            if 'revMajor' not in header.attrib:
                checker_data.checker.gen_issue(IssueLevel.ERROR,
                                        f'Cannot determine {format_name} version. <header> has no attribute revMajor.',
                                        create_location_from_element(header))
                return False

            if 'revMinor' not in header.attrib:
                checker_data.checker.gen_issue(IssueLevel.ERROR,
                                        f'Cannot determine {format_name} version. <header> has no attribute revMinor.',
                                        create_location_from_element(header))
                return False

            major = header.attrib['revMajor']
            minor = header.attrib['revMinor']
            try:
                major = int(major)
                minor = int(minor)
            except:
                logging.exception(f'Could not determine {format_name} version.')
                checker_data.checker.gen_issue(IssueLevel.ERROR, f'Cannot determine {format_name} version. Version is not parsable to int')
                return False
    except:
        logging.exception(f'Could not determine {format_name} version.')
        checker_data.checker.gen_issue(IssueLevel.ERROR, f'Cannot determine {format_name} version.')
        return False

    checker_data.version = major, minor # set version in checker data
    return True


def get_checker_id():
    return 'check get version'


def get_description():
    return f'check if file version is readable.'


def check(checker_data: CheckerData) -> bool:
    return check_version(checker_data)
