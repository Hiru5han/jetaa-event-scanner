import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CSVComparator:
    def __init__(self, list1, list2):
        self.list1 = list1
        self.list2 = list2

    def compare(self):
        logger.debug("Comparison started")
        differences = {"in_first_not_in_second": [], "in_second_not_in_first": []}
        logger.debug(f"Differences before comparison: {differences}")

        try:
            list1_lines = [str(item) for item in self.list1]
            logger.debug(f"List 1: {list1_lines}")

            list2_lines = [str(item) for item in self.list2]
            logger.debug(f"List 2: {list2_lines}")
        except Exception as convert_to_string_error:
            logger.error(f"Error converting lines to string: {convert_to_string_error}")

        try:
            logger.debug("Appending to list 1")
            for line in list1_lines:
                if line not in list2_lines:
                    differences["in_first_not_in_second"].append(line)
            logger.debug("Appending to list 2")
            for line in list2_lines:
                if line not in list1_lines:
                    differences["in_second_not_in_first"].append(line)
        except Exception as dict_append_error:
            logger.error(
                f"Error appending to differences dictionary: {dict_append_error}"
            )

        logger.debug(f"Differences after comparison: {differences}")

        return differences
