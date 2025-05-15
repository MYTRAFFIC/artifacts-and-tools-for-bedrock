athena_query = {
    "toolSpec": {
        "name": "athena_query",
        "description": """Executes SQL queries against Amazon Athena tables and returns the results.
- This tool can be used to query data stored in Amazon S3 using standard SQL.
- You can list available databases, tables, and get table schemas to help formulate your queries.
- Results are returned as CSV or JSON data that can be further processed or analyzed.
- Always use proper SQL syntax for Athena, which is based on Presto.
- For large datasets, consider using LIMIT to restrict the number of rows returned.
- Include appropriate WHERE clauses to filter data when possible.
- For complex queries, break them down into simpler steps and explain your approach.
""",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The action to perform: 'execute_query', 'list_databases', 'list_tables', or 'get_table_schema'",
                        "enum": ["execute_query", "list_databases", "list_tables", "get_table_schema"]
                    },
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute (required for 'execute_query' action)"
                    },
                    "database": {
                        "type": "string",
                        "description": "The Athena database to query (required for 'execute_query', 'list_tables', and 'get_table_schema' actions)"
                    },
                    "table": {
                        "type": "string",
                        "description": "The table name (required for 'get_table_schema' action)"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "The format of the output (csv or json)",
                        "enum": ["csv", "json"],
                        "default": "csv"
                    }
                },
                "required": ["action"]
            }
        }
    }
}

code_interpreter = {
    "toolSpec": {
        "name": "code_interpreter",
        "description": """Runs self-contained code in a new Python 3.12 Jupyter notebook.
- This tool can be used to perform various tasks, including data analysis, data visualization, machine learning and computer vision.
- The code executed by this tool does not have internet access. 
- Don't use URLs especially HTTP or HTTPS and APIs in the code.
- Do not install any additional libraries or other software beyond the supported libraries listed below.
- Code must be executable, correct, and self-contained. All variables must be defined within the code block. Verify the code to ensure it is correct and complete. If the code is incorrect or incomplete, rewrite it and verify again.
- Each code block should be self-contained and should not rely on variables or data from previous cells. Always write the code as if it is the first and only cell in the notebook.
- Results must always be rendered in the Jupyter notebook cell output.
- Supported additional libraries: pandas, numpy, matplotlib, scikit-learn, seaborn, scipy, pillow, opencv, geopandas, pyarrow, imageio, Faker.
- Always import libraries using the following conventions: import pandas as pd, import numpy as np, import matplotlib.pyplot as plt, import seaborn as sns, import cv2 (for opencv).
- When working with OpenCV images, always display them using matplotlib and use the FONT_HERSHEY_SIMPLEX font for text. For PIL use ImageFont.load_default()
- To handle data files like CSV or Excel, first, run the tool to read the file and display the schema (e.g., `df = pd.read_csv('file.csv')` followed by `print(df.head())` or `print(df.info())`).
- Include the complete and updated code without any truncation or minimization. Don't use "// rest of the code remains the same...".
- Specify all generated files in the output_files argument

# Don't use the tool for:
- Simple, informational, or short content, such as brief code snippets, mathematical equations, or small examples.
- Primarily explanatory, instructional, or illustrative content, such as examples provided to clarify a concept
- Conversational or explanatory content that doesn't represent executing code
- Never use tools for creating artifacts. Use the x-artifact tag for that purpose.
- Never use tools for React, Typescript, or HTML code. Use the x-artifact tag for that purpose.
""",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to run",
                    },
                    "output_files": {
                        "type": "array",
                        "description": "File names of files that the code will generate. This will be used to download the files after the code execution.",
                        "items": {
                            "type": "string",
                            "description": "File name with extension.",
                        },
                    },
                },
                "required": ["code"],
            }
        },
    }
}

web_search = {
    "toolSpec": {
        "name": "web_search",
        "description": "Searches the web for information using a search query. It can also crawl URLs for information.",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "urls": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "URLs to crawl for information.",
                        },
                    },
                },
                "required": [],
            }
        },
    }
}


class ConverseSpecification:
    def __init__(self):
        self.code_interpreter = code_interpreter
        self.web_search = web_search
        self.athena_query = athena_query


converse_tools = ConverseSpecification()
