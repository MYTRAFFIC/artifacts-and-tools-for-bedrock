import traceback
from docs_tool import DatabaseDocumentationTool


def handler(event, context):
    try:
        # Extract the input parameters
        name = event.get("name")
        input_params = event.get("input", {})

        if name != "database_docs":
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

        # Initialize the documentation tool
        docs_tool = DatabaseDocumentationTool()

        # Execute the requested action
        if action == "get_database_overview":
            overview = docs_tool.get_database_overview()
            return {
                "status": "success",
                "content": {
                    "text": "Here's an overview of available databases:",
                    "data": overview,
                },
            }

        elif action == "get_database_info":
            database = input_params.get("database")
            if not database:
                return {
                    "status": "error",
                    "content": {
                        "text": "Database name is required for get_database_info action"
                    },
                }

            info = docs_tool.get_database_info(database)
            if "error" in info:
                return {
                    "status": "error",
                    "content": {"text": info["error"]},
                }

            return {
                "status": "success",
                "content": {
                    "text": f"Here's detailed information about database '{database}':",
                    "data": info,
                },
            }

        elif action == "get_table_info":
            database = input_params.get("database")
            table = input_params.get("table")

            if not database or not table:
                return {
                    "status": "error",
                    "content": {
                        "text": "Both database and table names are required for get_table_info action"
                    },
                }

            info = docs_tool.get_table_info(database, table)
            if "error" in info:
                return {
                    "status": "error",
                    "content": {"text": info["error"]},
                }

            return {
                "status": "success",
                "content": {
                    "text": f"Here's detailed information about table '{table}' in database '{database}':",
                    "data": info,
                },
            }

        elif action == "search_tables":
            keyword = input_params.get("keyword")
            if not keyword:
                return {
                    "status": "error",
                    "content": {"text": "Keyword is required for search_tables action"},
                }

            results = docs_tool.search_tables(keyword)
            if not results:
                return {
                    "status": "success",
                    "content": {
                        "text": f"No tables found matching keyword '{keyword}'"
                    },
                }

            return {
                "status": "success",
                "content": {
                    "text": f"Found {len(results)} tables matching keyword '{keyword}':",
                    "data": results,
                },
            }

        elif action == "get_common_joins":
            joins = docs_tool.get_common_joins()
            return {
                "status": "success",
                "content": {
                    "text": "Here are some common join patterns between tables:",
                    "data": joins,
                },
            }

        else:
            return {
                "status": "error",
                "content": {"text": f"Invalid action: {action}"},
            }

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        print(traceback.format_exc())
        return {
            "status": "error",
            "content": {"text": f"Error processing request: {str(e)}"},
        }
