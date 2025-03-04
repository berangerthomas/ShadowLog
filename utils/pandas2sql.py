import sqlite3

import pandas as pd


class Pandas2SQL:
    """
    Classe pour convertir un DataFrame pandas en table SQLite
    avec détection automatique des types de colonnes.
    """

    def __init__(self, db_path=":memory:"):
        """
        Initialise la connexion à la base de données SQLite

        Args:
            db_path (str): Chemin vers le fichier de base de données SQLite
                           (par défaut utilise une base de données en mémoire)
        """
        self.db_path = db_path

    def _get_sqlite_type(self, pandas_dtype):
        """
        Convertit un type pandas en type SQLite approprié

        Args:
            pandas_dtype: Type pandas

        Returns:
            str: Type SQLite correspondant
        """
        if pd.api.types.is_integer_dtype(pandas_dtype):
            return "INTEGER"
        elif pd.api.types.is_float_dtype(pandas_dtype):
            return "REAL"
        elif pd.api.types.is_bool_dtype(pandas_dtype):
            return "INTEGER"  # SQLite n'a pas de type booléen, utilise INTEGER (0/1)
        elif pd.api.types.is_datetime64_dtype(pandas_dtype):
            return "TIMESTAMP"
        else:
            return "TEXT"  # Pour les types object, string, category, etc.

    def create_table(self, df, table_name, if_exists="replace", primary_key=None):
        """
        Crée une table SQLite basée sur un DataFrame pandas

        Args:
            df (pandas.DataFrame): DataFrame à convertir
            table_name (str): Nom de la table à créer
            if_exists (str): Action si la table existe ('fail', 'replace', 'append')
            primary_key (str): Nom de la colonne à définir comme clé primaire (optionnel)
        """
        # Création du schéma de table basé sur les types de colonnes
        columns = []
        for col_name, dtype in df.dtypes.items():
            sqlite_type = self._get_sqlite_type(dtype)
            col_def = f'"{col_name}" {sqlite_type}'
            if primary_key and col_name == primary_key:
                col_def += " PRIMARY KEY"
            columns.append(col_def)

        # Création de la requête SQL
        create_query = f'CREATE TABLE "{table_name}" ({", ".join(columns)})'

        # Connexion et création de la table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if if_exists == "replace":
                cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            elif if_exists == "fail":
                cursor.execute(
                    f'SELECT name FROM sqlite_master WHERE type="table" AND name="{table_name}"'
                )
                if cursor.fetchone():
                    raise ValueError(f"La table '{table_name}' existe déjà.")

            cursor.execute(create_query)

            # Insertion des données
            df.to_sql(table_name, conn, if_exists="append", index=False)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
