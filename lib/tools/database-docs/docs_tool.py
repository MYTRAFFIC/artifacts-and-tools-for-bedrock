from doc import DOC


class DatabaseDocumentationTool:
    """
    Tool to provide documentation about available databases, tables, and their relationships
    to help LLMs make better decisions about which queries to execute.
    """

    def get_documentation(self) -> str:
        return DOC
