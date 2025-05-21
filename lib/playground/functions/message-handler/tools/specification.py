database_docs = {
    "toolSpec": {
        "name": "database_docs",
        "description": """Provides comprehensive documentation about available databases, tables, and their relationships to help formulate effective queries.
Key capabilities:
- Explore the complete data model before running queries with athena_query
- Get detailed information about database tables including schemas, key columns, and partitioning
- Understand relationships between tables and common join patterns
- Discover example queries for common analytical tasks
- Search for relevant tables based on keywords in names or descriptions
- Get suggested queries for specific analytical tasks based on data model

Best practices for spatial data analysis:
1. First use this tool to understand the data model and available tables
2. Look for common join patterns and example queries relevant to your task
3. Examine table partitioning schemes to optimize query performance
4. Then use athena_query to execute your refined queries

Common use cases:
- Understanding available data sources for a new analysis
- Finding tables containing specific metrics or dimensions
- Learning how geographical entities relate to each other
- Getting schema details before writing complex joins
""",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The action to perform : 'get_documentation' (read all doc)",
                        "enum": [
                            "get_documentation",
                        ],
                    },
                },
                "required": ["action"],
            }
        },
    }
}

athena_query = {
    "toolSpec": {
        "name": "athena_query",
        "description": """Executes SQL queries against Amazon Athena tables and returns the results.
- This tool can be used to query data stored in Amazon S3 using standard SQL.
- You can list available databases, tables, and get table schemas to help formulate your queries.
- Results are returned as CSV stored in s3 that can be further processed or analyzed with the code interpreter tool.
- Always use proper SQL syntax for Athena, which is based on Presto.
- For large datasets, consider using LIMIT to restrict the number of rows returned.
- Include appropriate WHERE clauses to filter data when possible particularly using partitioning columns to avoid large queries.
- For complex queries, break them down into simpler steps and explain your approach.
- When performing a cross join, the smaller dataset should be always right
""",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The action to perform: 'execute_query'",
                        "enum": [
                            "execute_query",
                        ],
                    },
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute (required for 'execute_query' action)",
                    },
                    "database": {
                        "type": "string",
                        "description": "The Athena database to query (required for 'execute_query' action)",
                    },
                },
                "required": ["action"],
            }
        },
    }
}

find_ev_charge_points_locations = {
    "toolSpec": {
        "name": "find_ev_charge_points_locations",
        "description": """Helper function to query the best charging point locations.
- Results are returned as CSV stored in s3 that can be further processed or analyzed with the code interpreter tool.
""",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The action to perform: e.g. 'find_ev_charge_points_locations'",
                        "enum": [
                            "list_poi_categories",
                            "find_ev_charge_points_locations",
                        ],
                    },
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute (required for 'execute_query' action)",
                    },
                    "database": {
                        "type": "string",
                        "description": "The Athena database to query (required for 'execute_query' action)",
                    },
                },
                "required": ["action"],
            }
        },
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
- Supported additional libraries: pandas, numpy, matplotlib, scikit-learn, seaborn, scipy, pillow, opencv, geopandas, pyarrow, imageio, Faker, s3fs.
- You can read files from s3 directly using pandas with pd.read_csv("s3://...") or pd.read_parquet("s3://...")
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
        self.database_docs = database_docs
        self.code_interpreter = code_interpreter
        self.web_search = web_search
        self.athena_query = athena_query


converse_tools = ConverseSpecification()
