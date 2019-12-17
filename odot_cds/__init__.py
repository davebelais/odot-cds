from . import client, cds501


# TABLES_DIRECTORY: str = os.path.abspath(os.path.dirname(__file__) + '/tables')
#
#
# def load_data_frame(
#     table_name: str = tables.CRASH
# ) -> pandas.DataFrame:
#     """
#     Load an ODOT-CDS table as an instance of `pandas.DataFrame`.
#     """
#     path: str = TABLES_DIRECTORY + '/{}.parquet'.format(table_name)
#     try:
#         return pandas.read_parquet(path)
#     except:
#         pass
