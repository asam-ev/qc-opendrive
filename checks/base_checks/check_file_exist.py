from result_report import IssueLevel, FileLocation
from checker_data import CheckerData

import logging


def check_exists(checker_data: CheckerData) -> bool:
    logging.info(get_checker_id())

    if not checker_data.file.exists():
        checker_data.checker.gen_issue(IssueLevel.ERROR, 'Given file does not exist.', [FileLocation(checker_data.file)])
        return False
    
    if not checker_data.file.is_file():
        checker_data.checker.gen_issue(IssueLevel.ERROR, 'Given file is not a file.', [FileLocation(checker_data.file)])
        return False

def get_checker_id():
    return 'check if file exists'


def get_description():
    return 'check if file exists and is valid.'


def check(checker_data: CheckerData) ->bool:
    return check_exists(checker_data)