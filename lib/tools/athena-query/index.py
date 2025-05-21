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
            result = athena_tool.execute_query(query, database)

            if not result["success"]:
                return {
                    "status": "error",
                    "content": {"text": f"Error executing query: {result['error']}"},
                }

            # Format the response
            response_text = f"Query executed successfully. Full result available at {result['file']}. First rows below\n\n{result['data_head']}"

            return {
                "status": "success",
                "content": {"text": response_text},
            }

        elif action == "find_ev_charge_points_locations":
            try:
                result = athena_tool.find_ev_charge_points_locations(**input_params)
            except Exception as e:
                print(traceback.print_exc())
                return {
                    "status": "error",
                    "content": {"text": str(e)},
                }

            if not result["success"]:
                return {
                    "status": "error",
                    "content": {"text": f"Error executing query: {result['error']}"},
                }

            # Format the response
            response_text = f"Function executed successfully. Full result available at {result['file']}. First rows below\n\n{result['data_head']}"

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
