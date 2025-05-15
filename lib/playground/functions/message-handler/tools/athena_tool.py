import os
import boto3
import pandas as pd
import time
from botocore.exceptions import ClientError

class AthenaQueryTool:
    def __init__(self, region_name=None):
        self.region_name = region_name or os.environ.get("AWS_REGION")
        self.athena_client = boto3.client('athena', region_name=self.region_name)
        self.s3_client = boto3.client('s3', region_name=self.region_name)
        self.output_location = os.environ.get("ATHENA_QUERY_RESULTS_LOCATION")
        
    def execute_query(self, query, database, output_format="csv"):
        """
        Execute an Athena query and return the results
        
        Args:
            query (str): The SQL query to execute
            database (str): The Athena database to query
            output_format (str): The format of the output (csv or json)
            
        Returns:
            dict: A dictionary containing the query results and metadata
        """
        try:
            # Start the query execution
            response = self.athena_client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={
                    'Database': database
                },
                ResultConfiguration={
                    'OutputLocation': self.output_location
                }
            )
            
            query_execution_id = response['QueryExecutionId']
            
            # Wait for the query to complete
            state = 'RUNNING'
            max_retries = 100
            retry_count = 0
            
            while (state == 'RUNNING' or state == 'QUEUED') and retry_count < max_retries:
                response = self.athena_client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )
                state = response['QueryExecution']['Status']['State']
                
                if state == 'FAILED':
                    error_message = response['QueryExecution']['Status'].get('StateChangeReason', 'Query failed')
                    return {
                        'success': False,
                        'error': error_message
                    }
                elif state == 'SUCCEEDED':
                    # Get the results
                    results = self.athena_client.get_query_results(
                        QueryExecutionId=query_execution_id
                    )
                    
                    # Get the S3 path of the results
                    s3_path = response['QueryExecution']['ResultConfiguration']['OutputLocation']
                    
                    # Parse the results into a pandas DataFrame
                    bucket, key = self._parse_s3_path(s3_path)
                    
                    # Download the results file
                    local_file = f"/tmp/{query_execution_id}.csv"
                    self.s3_client.download_file(bucket, key, local_file)
                    
                    # Read the results into a DataFrame
                    df = pd.read_csv(local_file)
                    
                    # Convert to the requested format
                    if output_format.lower() == 'json':
                        result_data = df.to_json(orient='records')
                    else:
                        result_data = df.to_csv(index=False)
                    
                    # Get column information
                    columns = []
                    for col in df.columns:
                        dtype = str(df[col].dtype)
                        columns.append({
                            'name': col,
                            'type': dtype
                        })
                    
                    # Clean up the local file
                    os.remove(local_file)
                    
                    return {
                        'success': True,
                        'data': result_data,
                        'format': output_format.lower(),
                        'rows': len(df),
                        'columns': columns,
                        'query_execution_id': query_execution_id,
                        'database': database
                    }
                
                # Sleep before retrying
                time.sleep(1)
                retry_count += 1
            
            if retry_count >= max_retries:
                return {
                    'success': False,
                    'error': 'Query timed out'
                }
            
        except ClientError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_databases(self):
        """
        List all available Athena databases
        
        Returns:
            list: A list of database names
        """
        try:
            response = self.athena_client.list_databases(
                CatalogName='AwsDataCatalog'
            )
            
            databases = [db['Name'] for db in response['DatabaseList']]
            return {
                'success': True,
                'databases': databases
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
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
                CatalogName='AwsDataCatalog',
                DatabaseName=database
            )
            
            tables = [table['Name'] for table in response['TableMetadataList']]
            return {
                'success': True,
                'tables': tables
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
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
                CatalogName='AwsDataCatalog',
                DatabaseName=database,
                TableName=table
            )
            
            columns = []
            for col in response['TableMetadata']['Columns']:
                columns.append({
                    'name': col['Name'],
                    'type': col['Type']
                })
            
            return {
                'success': True,
                'table': table,
                'database': database,
                'columns': columns
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_s3_path(self, s3_path):
        """
        Parse an S3 path into bucket and key
        
        Args:
            s3_path (str): The S3 path
            
        Returns:
            tuple: A tuple containing the bucket and key
        """
        path = s3_path.replace('s3://', '')
        bucket, key = path.split('/', 1)
        return bucket, key
