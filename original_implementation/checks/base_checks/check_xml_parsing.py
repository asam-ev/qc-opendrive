from result_report import IssueLevel, FileLocation
from checker_data import CheckerData 
from lxml import etree

import logging


def check_read_XML(checker_data: CheckerData) -> bool:
    logging.info(get_checker_id())

    try: 
        with open(checker_data.file, 'r') as f:
            _ = f.read() #  set root for further test
    except:
        logging.exception(f'Cannot read file {checker_data.file.absolute()}')
        checker_data.checker.gen_issue(IssueLevel.ERROR, 'Given file cannot be read.', [FileLocation(checker_data.file)])
        return False
    
        # run checks
    try: 
        checker_data.data = etree.parse(str(checker_data.file), etree.XMLParser(dtd_validation=False))
    except:
        logging.exception(f'Cannot parse XML from file {checker_data.file.absolute()}')
        checker_data.checker.gen_issue(IssueLevel.ERROR,
                                      'Given file cannot be parsed to XML.',
                                      [FileLocation(checker_data.file)])

    return True

def get_checker_id():
    return 'check if xml readable'


def get_description():
    return 'check if xml readable.'


def check(checker_data: CheckerData) ->bool:
    return check_read_XML(checker_data)