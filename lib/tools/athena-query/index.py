import traceback
from aws_lambda_powertools import Logger

from athena_tool import AthenaQueryTool

logger = Logger(log_uncaught_exceptions=True)


@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    try:
        # Extract the input parameters
        name = event.get("name")
        input_params = event.get("input", {})

        if name != "athena_query":
            return {
                "status": "error",
                "content": {"text": f"Invalid tool name: {name}"},
            }

        # Get the action to perform
        action = input_params.get("action")
        if not action:
            return {
                "status": "error",
                "content": {"text": "Action is required"},
            }

        # Initialize the Athena query tool
        athena_tool = AthenaQueryTool()

        # Execute the requested action
        if action == "execute_query":
            # Get the required parameters
            query = input_params.get("query")
            database = input_params.get("database")
            output_format = input_params.get("output_format", "csv")

            if not query:
                return {
                    "status": "error",
                    "content": {"text": "Query is required for execute_query action"},
                }

            if not database:
                return {
                    "status": "error",
                    "content": {
                        "text": "Database is required for execute_query action"
                    },
                }

            # Execute the query
            result = athena_tool.execute_query(query, database, output_format)

            if not result["success"]:
                return {
                    "status": "error",
                    "content": {"text": f"Error executing query: {result['error']}"},
                }

            # Format the response
            response_text = f"Query executed successfully. Retrieved rows from {result['database']}.\n\n"

            return {
                "status": "success",
                "content": {"text": response_text},
                "extra": {"output_files": [result["file"]]},
            }

        elif action == "list_databases":
            # List all available databases
            result = athena_tool.list_databases()

            if not result["success"]:
                return {
                    "status": "error",
                    "content": {"text": f"Error listing databases: {result['error']}"},
                }

            # Format the response
            response_text = "Available databases:\n"
            for db in result["databases"]:
                response_text += f"- {db}\n"

            return {
                "status": "success",
                "content": {"text": response_text},
            }

        elif action == "list_tables":
            # Get the required parameters
            database = input_params.get("database")

            if not database:
                return {
                    "status": "error",
                    "content": {"text": "Database is required for list_tables action"},
                }

            # List all tables in the database
            result = athena_tool.list_tables(database)

            if not result["success"]:
                return {
                    "status": "error",
                    "content": {"text": f"Error listing tables: {result['error']}"},
                }

            # Format the response
            response_text = f"Tables in database '{database}':\n"
            for table in result["tables"]:
                response_text += f"- {table}\n"

            return {
                "status": "success",
                "content": {"text": response_text},
            }

        elif action == "get_table_schema":
            # Get the required parameters
            database = input_params.get("database")
            table = input_params.get("table")

            if not database:
                return {
                    "status": "error",
                    "content": {
                        "text": "Database is required for get_table_schema action"
                    },
                }

            if not table:
                return {
                    "status": "error",
                    "content": {
                        "text": "Table is required for get_table_schema action"
                    },
                }

            # Get the table schema
            result = athena_tool.get_table_schema(database, table)

            if not result["success"]:
                return {
                    "status": "error",
                    "content": {
                        "text": f"Error getting table schema: {result['error']}"
                    },
                }

            # Format the response
            response_text = f"Schema for table '{table}' in database '{database}':\n"
            for col in result["columns"]:
                response_text += f"- {col['name']} ({col['type']})\n"

            return {
                "status": "success",
                "content": {"text": response_text},
            }

        else:
            return {
                "status": "error",
                "content": {"text": f"Invalid action: {action}"},
            }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "content": {"text": f"Error processing request: {str(e)}"},
        }
