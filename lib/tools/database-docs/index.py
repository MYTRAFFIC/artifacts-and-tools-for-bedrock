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
        if action == "get_documentation":
            documentation = docs_tool.get_documentation()
            return {
                "status": "success",
                "content": {
                    "text": f"Full Documentation of tables: {documentation}",
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
