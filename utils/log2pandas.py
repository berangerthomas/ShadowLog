import pandas as pd
from dateutil.parser import parse

from config.log_definitions import log_definitions


class LogParser:
    """
    A class that takes a log file path and a log definition (for example from log_definitions),
    then parses the file and returns a pandas DataFrame containing the extracted data.
    """

    def __init__(self, file_path, log_type):
        self.file_path = file_path
        self.log_definition = log_definitions[log_type]

    def parse_line(self, line):
        """Parse a line from the log file using the provided definition."""
        # Start by replacing [ and ] with spaces
        line = line.replace("[", " ").replace("]", " ")
        tokens = line.strip().split()
        # Ignore the line if it does not contain enough tokens
        if len(tokens) < len(self.log_definition["fields"]):
            return None

        entry = {}
        for field in self.log_definition["fields"]:
            pos = field["pos"]

            # Extract the value according to the indicated position
            if isinstance(pos, slice):
                value = " ".join(tokens[pos])
            else:
                try:
                    value = tokens[pos]
                except IndexError:
                    value = None

            # Type conversion
            if "type" in field:
                typ = field["type"]
                if typ == "datetime":
                    # Try to parse the date with dateutil.parser
                    try:
                        value = parse(value)
                    except ValueError:
                        # If the date is not parsable, try several formats
                        value = None
                elif typ == "direction":
                    value = "download" if value == "o" else "upload"
                else:
                    try:
                        value = typ(value)
                    except Exception:
                        pass

            entry[field["name"]] = value

        return entry

    def parse_file(self):
        """Iterate through the entire log file and return a pandas DataFrame containing the parsed entries."""
        data = []
        with open(self.file_path, "r") as f:
            for line in f:
                parsed = self.parse_line(line)
                if parsed:
                    data.append(parsed)

        return pd.DataFrame(data)
