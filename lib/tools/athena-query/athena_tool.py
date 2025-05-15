import os
import traceback
import boto3
import awswrangler as wr
import pandas as pd


class AthenaQueryTool:
    def __init__(self, region_name=None):
        self.region_name = region_name or os.environ.get("AWS_REGION")
        self.athena_client = boto3.client("athena", region_name=self.region_name)
        self.s3_client = boto3.client("s3", region_name=self.region_name)
        self.athena_workgroup = os.environ.get("ATHENA_WORKGROUP")

    def execute_query(self, query: str, database: str):
        """
        Execute an Athena query and return the results

        Args:
            query (str): The SQL query to execute
            database (str): The Athena database to query

        Returns:
            dict: A dictionary containing the query results and metadata
        """
        try:
            response = wr.athena.start_query_execution(
                sql=query,
                database=database,
                workgroup=self.athena_workgroup,
                athena_query_wait_polling_delay=1,
                wait=True,
            )
            s3_output_path = response["ResultConfiguration"]["OutputLocation"]
            # don't truncate to leave all infos to the LLM
            with pd.option_context(
                "display.max_rows",
                None,
                "display.max_columns",
                None,
                "display.max_colwidth",
                None,
                "display.width",
                None,
            ):
                data_head = next(
                    wr.s3.read_csv(path=s3_output_path, chunksize=10)
                ).to_string(index=False)

            return {
                "success": response["Status"].get("State", "") == "SUCCEEDED",
                "file": s3_output_path,
                "data_head": data_head,
                "query_execution_id": response["QueryExecutionId"],
                "database": database,
            }
        except Exception as e:
            print(traceback.print_exc())
            return {"success": False, "error": str(e)}

    def list_databases(self):
        """
        List all available Athena databases

        Returns:
            list: A list of database names
        """
        return {
            "success": True,
            "databases": [
                "pipeline_data_v2",
                "geography",
                "pois",
                "dev_ev_connect_oja_ev_charger_features",
            ],
        }

    def list_tables(self, database):
        """
        List all tables in a database

        Args:
            database (str): The database name

        Returns:
            list: A list of table names
        """
        try:
            response = self.athena_client.list_table_metadata(
                CatalogName="AwsDataCatalog", DatabaseName=database
            )

            tables = [table["Name"] for table in response["TableMetadataList"]]
            return {"success": True, "tables": tables}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_table_schema(self, database, table):
        """
        Get the schema of a table

        Args:
            database (str): The database name
            table (str): The table name

        Returns:
            dict: A dictionary containing the table schema
        """
        try:
            response = self.athena_client.get_table_metadata(
                CatalogName="AwsDataCatalog", DatabaseName=database, TableName=table
            )

            columns = [
                {"name": col["Name"], "type": col["Type"]}
                for col in response["TableMetadata"]["Columns"]
            ]
            partitions = [
                {"name": col["Name"], "type": col["Type"]}
                for col in response["TableMetadata"]["PartitionKeys"]
            ]

            return {
                "success": True,
                "table": table,
                "database": database,
                "columns": columns,
                "partitions": partitions,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_s3_path(self, s3_path):
        """
        Parse an S3 path into bucket and key

        Args:
            s3_path (str): The S3 path

        Returns:
            tuple: A tuple containing the bucket and key
        """
        path = s3_path.replace("s3://", "")
        bucket, key = path.split("/", 1)
        return bucket, key
