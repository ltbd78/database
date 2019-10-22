# Read Me
### Linsu Han (lh2910)

For any ambiguities, call (317) 515-1299; I offer 24/7 live tech support for my code. Will run any additional test cases real time over Skype, including demo on extra credit.

The general structure of this project is:  
`dbutils` -> `RDBDataTable` -> `data_table_adaptor` -> `app` -> `PostMan`/`Localhost`

Documented changes:

- `dbutils`
    - `create_select()`
        - added offset and limit for extra credit problem
- `RDBDataTable` 
    - `__init()__`
        - line 39: added `db_name = connect_info['db]` check
        - changed `connect_info` to local var
        - initialized all object variables
    - `find_by_template`
        - added limit and offset support
    - implemented
        - `get_primary_key_columns()`
        - `get_row_count()`
        - `get_sample_rows()`
        - `get_rows()`
- `data_table_adaptor`
    - added `_default_connect_info` with unspecified db name
    - `get_rdb_table`
        - initialized connect_info
    - implemented
        - `get_tables()`
        - `get_databases()`
- `app`
    - implemented
        - `dbs()` - gets lists of databases
        - `tbls()` - gets list of tables in given database
        - `resource_by_id()` - select, update, delete by primary key
        - `get_resource()` - select, insert by template
        