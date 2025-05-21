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
                data_head = next(wr.s3.read_csv(path=s3_output_path, chunksize=10))
                if "geometry_4326" in data_head.columns:
                    data_head["geometry_4326"] = data_head["geometry_4326"].apply(
                        lambda x: x[:10]
                    )
                data_head_str = data_head.to_string(index=False)

            return {
                "success": response["Status"].get("State", "") == "SUCCEEDED",
                "file": s3_output_path,
                "data_head": data_head_str,
                "query_execution_id": response["QueryExecutionId"],
                "database": database,
            }
        except Exception as e:
            print(traceback.print_exc())
            return {"success": False, "error": str(e)}
