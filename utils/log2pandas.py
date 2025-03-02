from datetime import datetime
import pandas as pd
from config.log_definitions import log_definitions


class LogParser:
    """
    Une classe qui prend en argument le chemin d'un fichier log et une définition
    de log (par exemple issue de log_definitions), puis parse le fichier et renvoie
    un DataFrame pandas contenant les données extraites.
    """

    def __init__(self, file_path, log_type):
        self.file_path = file_path
        self.log_definition = log_definitions[log_type]

    def parse_line(self, line):
        """Parse une ligne du fichier log en utilisant la définition fournie."""
        tokens = line.strip().split()
        # On ignore la ligne si elle ne contient pas assez de tokens
        if len(tokens) < len(self.log_definition["fields"]):
            return None

        entry = {}
        for field in self.log_definition["fields"]:
            pos = field["pos"]

            # Extraction de la valeur selon la position indiquée
            if isinstance(pos, slice):
                value = " ".join(tokens[pos])
            else:
                try:
                    value = tokens[pos]
                except IndexError:
                    value = None

            # Conversion du type
            if "type" in field:
                typ = field["type"]
                if typ == "datetime":
                    try:
                        # Format typique utilisé dans nos logs
                        value = datetime.strptime(value, "%a %b %d %H:%M:%S %Y")
                    except Exception:
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
        """Parcourt tout le fichier log et renvoie un DataFrame pandas contenant les entrées parse."""
        data = []
        with open(self.file_path, "r") as f:
            for line in f:
                parsed = self.parse_line(line)
                if parsed:
                    data.append(parsed)

        return pd.DataFrame(data)
