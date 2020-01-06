# !/usr/bin python3

"""
This script will prepare source dimensions as pickle files
"""
import functools
import os
import csv
import sqlite3
from collections import OrderedDict, namedtuple
from decimal import Decimal

import iso8601 as iso8601
import pandas
from typing import Iterable, Optional, Union, Tuple, List

# Constants
REPOSITORY_DIRECTORY = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
PICKLE_TABLES_DIRECTORY = REPOSITORY_DIRECTORY + '/odot_cds/dimensions'
SOURCES_DIRECTORY = REPOSITORY_DIRECTORY + '/sources'
CDS510_SQLLITE_PATH = SOURCES_DIRECTORY + '/cds510.db'
CDS501_CSV_DIRECTORY = SOURCES_DIRECTORY + '/cds501'
CDS501_FIELDS_CSV_PATH = SOURCES_DIRECTORY + '/cds501-fields.csv'
CDS501_CSV_FILE_NAME = 'CDS501.txt'
CDS_REC_TYP_CD_TABLES = {
    '1': 'crash',
    '2': 'vhcl',
    '3': 'partic'
}
CDS_EXCLUDE_SQLITE_TABLES = {
    'crash_key_xref',
    'crash'
}


def find_csvs(path: str, file_name: str) -> Iterable[str]:
    """
    Search for files named `file_name` (which are actually CSVs) and return
    their file paths
    """
    if path.split('/')[-1].split('\\')[-1] == file_name:
        yield path
    elif os.path.isdir(path):
        for name in sorted(os.listdir(path)):
            for data_file_path in find_csvs(
                path + '/' + name,
                file_name
            ):
                yield data_file_path


def format_field_value(
    value: str,
    format: str
) -> Optional[Union[bool, int, float, str]]:
    """
    Format a value based on a format string taken from documentation for the
    CDS501 extraxt.

    Parameters:

        - value (str):

          The `str` representation of the value, as read from the CSV.

        - format (str):

          A text description of the field format.
    """
    if value is None:
        return value
    value = value.strip()
    if not value:
        return None
    if 'char' in format:
        return value
    if 'int' in format:
        return int(value)
    if 'decimal' in format:
        return Decimal(value)
    if 'float' in format:
        return float(value)
    if 'bit' in format:
        return bool(int(value))
    raise ValueError('Unrecognized format: ' + format)


def format_field_type(
    format: str
) -> type:
    """
    Format a value based on a format string taken from documentation for the
    CDS501 extraxt.

    Parameters:

        - value (str):

          The `str` representation of the value, as read from the CSV.

        - format (str):

          A text description of the field format.
    """
    if 'char' in format:
        return str
    if 'int' in format:
        return int
    if 'decimal' in format:
        return Decimal
    if 'float' in format:
        return float
    if 'bit' in format:
        return bool
    raise ValueError('Unrecognized format: ' + format)


@functools.lru_cache()
def get_cds501_fields(
    csv_path: str = CDS501_FIELDS_CSV_PATH
) -> Iterable[dict]:
    """
    Read a CSV describing the CDS501 fields (in the order of their row index).

    Each row in this CSV should have the following properties:

        - Name:

          The column name to be used for this field.

        - Label:

          A user-friendly name for the field.

        - Format:

          A description of the data format.

        - Description:

          A description of the field.

        - Tables:

          A comma-separated list of the dimensions in which this field appears.
    """
    return tuple(read_csv(csv_path))


def read_cds501_csv_table(
    table: str,
    csv_path: str,
    fields_csv_path: str = CDS501_FIELDS_CSV_PATH
) -> Iterable[dict]:
    """
    Read a single CDS501 CSV, looking for records corresponding to the given
    table.

    Parameters:

        - table (str):

          The name of the table to return records for

        - csv_path (str):

          The file path where the CDS501 CSV is located.

        - fields_csv_path (str):

          The file path where the CDS501 field definition CSV is located.
    """
    fields = get_cds501_fields(fields_csv_path)
    with open(csv_path, 'r') as txt_file:
        for values in csv.reader(
            txt_file
        ):
            # Only yield records corresponding to the desired table
            if CDS_REC_TYP_CD_TABLES[values[1]] != table:
                continue
            row = OrderedDict()
            for index, value in enumerate(values):
                field = fields[index]
                # Exclude fields not applicable to this table
                if table not in field['Tables']:
                    continue
                row[field['Name'].lower()] = format_field_value(
                    value, field['Format']
                )
            yield row


def read_csv(csv_path: str, **kwargs) -> Iterable[dict]:
    """
    Read a CSV.

    Parameters:

        - csv_path (str): The file path where the CSV file is located.

        - **kwargs (dict):

          Any additional eyword arguments provided will be used to initialize
          an instance of `csv.DictReader`
    """
    with open(csv_path, 'r') as txt_file:
        for row in csv.DictReader(
            txt_file,
            **kwargs
        ):
            yield row


def read_cds501_csvs_table(
    table: str,
    csv_directory: str = CDS501_CSV_DIRECTORY,
    file_name: str = CDS501_CSV_FILE_NAME
) -> Iterable[OrderedDict]:
    """
    Search for CDS501 CSV files, and parse them for use in a data frame.

    Parameters:

        - csv_directory (str): The directory under which to search for CSVs.
    """
    for csv_path in find_csvs(
        csv_directory,
        file_name
    ):
        for row in read_cds501_csv_table(table, csv_path):
            # Assemble a `datetime` from parts for rows in the "crash" table
            if table == 'crash':
                row['crash_dt'] = iso8601.parse_date(
                    '%s-%s-%sT%s' % (
                        row['crash_yr_no'],
                        ('00' + row['crash_mo_no'])[-2:],
                        ('00' + row['crash_day_no'])[-2:],
                        (
                            '00%s:00' % row['crash_hr_no']
                            if row['crash_hr_no'] <= '24' else
                            '23:59'
                        )[-5:]
                    ),
                    default_timezone=None
                )
            yield row


def cds501_csvs2pickle(
    source_data_directory: str = CDS501_CSV_DIRECTORY,
    pickle_directory: str = PICKLE_TABLES_DIRECTORY,
    source_file_name: str = CDS501_CSV_FILE_NAME
) -> List[str]:
    """
    Convert one or more CDS501 CSV extracts to a pickle data file.

    Parameters:

        - source_data_directory (str):

          The directory path in which to search for CDS501 CSV files.

        - pickle_path (str):

          The path where the pickle file should be written.

        - source_file_name (str):

          The file name (not including parent directories) to search for.
    """
    paths: List[str] = []
    for table in CDS_REC_TYP_CD_TABLES.values():
        path: str = '%s/%s.pickle' % (pickle_directory, table)
        write_pickle(
            path,
            read_cds501_csvs_table(
                table,
                source_data_directory,
                source_file_name
            )
        )
        paths.append(path)
    return paths


def csv2pickle(
    source_path: str,
    pickle_path: Optional[str] = None
) -> str:
    """
    Convert a CSV file to a pickled data frame.

    Parameters:

        - source_path (str):

          The path where the source CSV is located.

        - pickle_path (str):

          The path where the pickle file should be written.
    """
    if not pickle_path:
        pickle_path = '%s/%s.pickle' % (
            PICKLE_TABLES_DIRECTORY,
            '.'.join(
                source_path.split('/')[-1].split('.')[:-1]
            )
        )
    write_pickle(
        pickle_path,
        read_csv(source_path)
    )
    return pickle_path


def write_pickle(
    path: str,
    data: Union[Iterable[dict], pandas.DataFrame]
) -> None:
    """
    Write dimensions to a pickle file.

    Parameters:

        - path (str):

          A file path where the pickle file should be written.

        - dimensions ([dict]|pandas.DataFrame):

          Either an iterable of dictionary instances, or a dimensions frame.
    """
    if isinstance(data, pandas.DataFrame):
        data_frame = data
    else:
        data_frame = pandas.DataFrame(data)
    data_frame.to_pickle(path)


def fetchall(
    cursor: sqlite3.Cursor
) -> str:
    """
    Given a database cursor, perform a `fetchall`--but yield instances
    of a *named tuple*, and convert date/time strings to `date` or `datetime`
    instances.
    """
    columns = tuple(
        description[0]
        for description in cursor.description
    )
    Row = namedtuple('Row', columns)
    for row in cursor.fetchall():
        yield Row(*(
            (
                iso8601.parse_date(value)
                if (
                    columns[index][-3:] == '_DT' and
                    (value is not None)
                ) else
                value
            )
            for index, value in enumerate(row)
        ))


def read_cds510(
    path: str = CDS510_SQLLITE_PATH
) -> Iterable[Tuple[str, pandas.DataFrame]]:
    """
    This procedure reads the CDS510 sqlite database and returns a dictionary
    mapping each table name to a data frame created from it's contents
    """
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    # Lookup the table names in the `sqlite_master` table
    cursor.execute(
        "select name from main.sqlite_master where type='table'"
    )
    # Select the contents of each table and create a data frame
    for table_name, in cursor.fetchall():
        query: str = 'select * from "main"."%s"' % table_name
        cursor.execute(query)
        rows = tuple(fetchall(cursor))
        if rows:
            columns = rows[0]._fields
            yield table_name, pandas.DataFrame(
                rows,
                columns=columns
            )


def csv510_sqlite2pickle(
    sqlite_path: str = CDS510_SQLLITE_PATH,
    pickle_directory: str = PICKLE_TABLES_DIRECTORY
) -> None:
    """
    Given the path to a CSV510 sqlite database--export all dimensions as pickle
    files.
    """
    with open('%s/cds501.py' % pickle_directory, 'w') as tables_init_io:
        for (
            table,  # type: str
            data_frame  # type: pandas.DataFrame
        ) in read_cds510(sqlite_path):
            tables_init_io.write(
                "%s: str = '%s'\n" % (
                    table,
                    table.lower()
                )
            )
            if table not in CDS_EXCLUDE_SQLITE_TABLES:
                write_pickle(
                    '%s/%s.pickle' % (pickle_directory, table.lower()),
                    data_frame
                )


def get_cds501_class_definition() -> str:
    lines: List[str] = [
        '@dataclass(unsafe_hash=True, frozen=True)',
        'class CDS501:\n'
    ]
    for field in get_cds501_fields():
        lines.append(
            (
                '    %s: %s'
                if field['Name'].lower() == 'crash_id' else
                '    %s: Optional[%s]'
            ) % (
                field['Name'].lower(),
                format_field_type(field['Format']).__name__
            )
        )
    return '\n'.join(lines)


def get_cds510_class_definitions() -> str:
    cds501_fields: Tuple[dict] = get_cds501_fields()
    lines: List[str] = []
    for table_name in CDS_REC_TYP_CD_TABLES.values():
        class_name: str = table_name.upper()[0] + table_name.lower()[1:]
        lines += [
            '@dataclass(unsafe_hash=True, frozen=True)',
            'class %s:\n' % class_name
        ]
        for field in cds501_fields:
            if table_name in field['Tables']:
                lines.append(
                    (
                        '    %s: %s'
                        if field['Name'].lower() == table_name + '_id' else
                        '    %s: Optional[%s]'
                    ) % (
                        field['Name'].lower(),
                        format_field_type(field['Format']).__name__
                    )
                )
        lines += ['', '']
    return '\n'.join(lines)




if __name__ == '__main__':
    # # Extract reference dimensions from the CDS510 sqlite database (converted from
    # # an MS Access .mdb).
    csv510_sqlite2pickle()
    # # The CDS510 will not have complete crash/vehicle/participant data, because
    # # it takes far too long to extract in this format, so we now look for
    # # CDS501 CSVs. These will have complete crash/vehicle/participant data--but
    # # will not have any of the reference dimensions.
    # cds501_csvs2pickle()
    # print(get_cds510_class_definitions())
