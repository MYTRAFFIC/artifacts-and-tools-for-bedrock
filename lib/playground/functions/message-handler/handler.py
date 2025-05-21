import os
import json
import traceback
import boto3
from common.sender import MessageSender
from common.system import system_messages
from tools import ToolProvider, ConverseToolExecutor, converse_tools
from common.files import (
    filter_inline_files,
    get_inline_file_data,
)
from common.session import load_session, save_session, create_dynamodb_session


AWS_REGION = os.environ["AWS_REGION"]
BEDROCK_REGION = os.environ.get("BEDROCK_REGION")
BEDROCK_MODEL = os.environ.get("BEDROCK_MODEL")
ARTIFACTS_ENABLED = os.environ.get("ARTIFACTS_ENABLED")
TOOL_CODE_INTERPRETER = os.environ.get("TOOL_CODE_INTERPRETER")
TOOL_WEB_SEARCH = os.environ.get("TOOL_WEB_SEARCH")
TOOL_ATHENA_QUERY = os.environ.get("TOOL_ATHENA_QUERY")
ATHENA_WORKGROUP = os.environ.get("ATHENA_WORKGROUP")
TOOL_DATABASE_DOCS = os.environ.get("TOOL_DATABASE_DOCS")

s3_client = boto3.client(
    "s3", region_name=AWS_REGION, endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com"
)
bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

provider = ToolProvider(
    {
        "code_interpreter": TOOL_CODE_INTERPRETER,
        "web_search": TOOL_WEB_SEARCH,
        "athena_query": TOOL_ATHENA_QUERY,
        "database_docs": TOOL_DATABASE_DOCS,
    }
)

tool_config = []
if TOOL_CODE_INTERPRETER:
    tool_config.append(converse_tools.code_interpreter)
if TOOL_WEB_SEARCH:
    tool_config.append(converse_tools.web_search)
if TOOL_ATHENA_QUERY:
    tool_config.append(converse_tools.athena_query)
if TOOL_DATABASE_DOCS:
    tool_config.append(converse_tools.database_docs)

PREPROMPT = """You are assisting a Commercial Developer at a Charge Point Operator (CPO). Your role is to help identify and prioritize locations for the potential deployment of electric vehicle (EV) charging stations.
You can use documentation and data sources to answer questions such as:
Example of questions
    - Find Top `n` places in `Region/City/Neighborhood` with the most potential for `type of EV charging` near `POI category` and rank them by `metric`.
How to Get Data:
    1. Identify the region of interest using geography.adjustment_zones, geography.cities, or geography.neighborhoods depending on the scope (region, city, neighborhood). Be cautious of cities split into subdivisions (e.g., Paris 01, Paris 02, etc.).
    2. Filter POIs by category: query pois.category_matrix to validate the correct 'category_3' for the user-requested category (e.g., supermarkets), then filter pois.enriched_pois by that category and the geographic area.
    3. Perform a spatial join between pois.enriched_pois and dev_geography_oja_ev_charger_features.h3_11 using spatial proximity and select the nearest h3_index for a POI.
    4. Join with dev_ev_connect_oja_ev_charger_features.station_selector_predictions_final_without_explanation to get prediction scores. Use the appropriate column for the charging type:
        - pred_rapid_score, pred_fast_score, pred_medium_score, or pred_slow_score and select the TOP n locations.
    5. Rank based on the user-specified metric, such as:
        - highways_and_major_roads_mean_aadt_within_100_m
        - population_density_habitants_per_km2
        - purchasing_power_per_capita
        if the metric is not available, maybe you can create it
Parameters to map:
    - type of charging → pred_{type}_score in station_selector_predictions_final_without_explanation
    - POI category → category_3 from pois.category_matrix
    - Region/City/Neighborhood → adjustment_zones.name, cities.name, or neighborhoods.name
    - Metric → any relevant ranking metric column from prediction table
    Tips:
    - Always use category_matrix to verify the POI category.
    - Avoid using text LIKE '%keyword%' for location filtering — use geography joins instead.
    - Minimize geometry calculations by filtering the dataset early.
    - Use ST_DWithin for accurate spatial proximity joins between POIs and H3 cells"""


def handle_message(logger, connection_id, user_id, body):
    logger.info(f"Received message for {user_id}")
    logger.info(body)
    sender = MessageSender(connection_id)

    try:
        session_id = body.get("session_id")
        event_type = body.get("event_type")

        if not session_id:
            raise ValueError("Session ID is required")

        if event_type == "HEARTBEAT":
            sender.send_heartbeat(BEDROCK_MODEL)
        elif event_type == "INTERRUPT":
            # Create a flag in the session to indicate interruption
            _, session = load_session(s3_client, user_id, session_id)
            session["interrupt"] = True
            save_session(s3_client, user_id, session_id, session)

            # Send a message to the client to indicate that interruption was requested
            sender.send_text(
                "Interruption requested. The model will stop generating as soon as possible."
            )
        elif event_type == "CONVERSE":
            files = body.get("files", [])
            message = body.get("message")

            new_session, session = load_session(s3_client, user_id, session_id)
            # Reset the interruption flag when starting a new conversation
            session["interrupt"] = False

            converse_messages = session.get("messages")
            tool_extra = session.get("tool_extra")
            inline_files = session.get("inline_files")

            files_to_inline = filter_inline_files(files, inline_files)
            inline_files.extend(files_to_inline)
            inline_files_data = get_inline_file_data(
                s3_client, user_id, session_id, files_to_inline
            )

            content = []
            if new_session:
                converse_messages.append(
                    {
                        "role": "system",
                        "content": PREPROMPT,
                    }
                )
            if message:
                content.append({"text": message})

            if inline_files_data:
                content.extend(
                    [
                        {
                            "image": {
                                "format": data["format"],
                                "source": {"bytes": data["data"]},
                            },
                        }
                        for data in inline_files_data
                    ]
                )
            if content:
                converse_messages.append(
                    {
                        "role": "user",
                        "content": content,
                    }
                )

            finish = converse_make_request_stream(
                sender,
                user_id,
                session_id,
                converse_messages,
                tool_extra,
                files,
                s3_client,  # Pass s3_client to check for interruption
            )

            if new_session:
                create_dynamodb_session(user_id, session_id, message)
            save_session(s3_client, user_id, session_id, session)

            sender.send_loop(finish)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    except Exception as e:
        logger.error(traceback.print_exc())
        logger.error(f"Error processing message: {e}")
        sender.send_error(str(e))

    return {"statusCode": 200, "body": json.dumps({"ok": True})}


def converse_make_request_stream(
    sender: MessageSender,
    user_id,
    session_id,
    converse_messages,
    tool_extra,
    files,
    s3_client,  # Added s3_client parameter
):
    file_names = [os.path.basename(file["file_name"]) for file in files]
    system = system_messages(
        ARTIFACTS_ENABLED == "1", s3_client, user_id, session_id, file_names
    )

    additional_params = {}
    if tool_config:
        additional_params["toolConfig"] = {"tools": tool_config}

    streaming_response = bedrock_client.converse_stream(
        modelId=BEDROCK_MODEL,
        system=system,
        messages=converse_messages,
        inferenceConfig={"maxTokens": 5120, "temperature": 0.5},
        **additional_params,
    )

    executor = ConverseToolExecutor(user_id, session_id, provider)
    chunk_count = 0
    for chunk in streaming_response["stream"]:
        # Check for interruption every 10 chunks
        if chunk_count % 10 == 0:
            # Load the session to check the interruption flag
            _, session = load_session(s3_client, user_id, session_id)
            if session.get("interrupt", False):
                sender.send_text("\n\n[Generation interrupted by user]")
                break

        chunk_count += 1
        if text := executor.process_chunk(chunk):
            sender.send_text(text)

    assistant_messages = executor.get_assistant_messages()
    converse_messages.extend(assistant_messages)

    if executor.execution_requested():
        tool_use_extra = sender.send_tool_running_messages(executor)
        tool_extra.update(tool_use_extra)

        executor.execute(s3_client, file_names)
        user_messages = executor.get_user_messages()
        converse_messages.extend(user_messages)

        tool_results_extra = sender.send_tool_finished_messages(executor)

        for tool_use_id, extra in tool_results_extra.items():
            tool_extra.get(tool_use_id, {}).update(extra)

        return False

    return True
