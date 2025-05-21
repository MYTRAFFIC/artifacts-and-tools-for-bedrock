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

    def find_ev_charge_points_locations(
        self,
        country: str,
        adjustment_zone_id: str,
        city_id: str,
        poi_categories: list[str],
    ):
        poi_radius_meters = 100
        if not adjustment_zone_id and not city_id:
            return {
                "success": False,
                "error": "you must specify either adjustment_zone_id or city_id",
            }
        quoted_poi_categories = ",".join([f"'{cat.lower()}'" for cat in poi_categories])
        if city_id:
            geographic_clause = f"c.city_id = '{city_id}'"
        else:
            geographic_clause = f"c.adjustment_zone_id = '{adjustment_zone_id}'"
        query = f"""
        WITH selected_pois AS (
            SELECT 
                p.poi_id, 
                p.title AS supermarket_name, 
                p.latitude, 
                p.longitude, 
                p.address,
                ST_POINT(p.longitude, p.latitude) AS poi_point
            FROM 
                pois.enriched_pois p
            JOIN 
                geography.neighborhoods n ON p.neighborhood_id = n.id AND p.country = n.country
            JOIN 
                geography.cities c ON n.city_id = c.id AND p.country = c.country
            WHERE 
                p.country = '{country}' 
                AND LOWER(p.category) IN ({quoted_poi_categories})
                AND {geographic_clause}
        ),
        h3_cells AS (
            SELECT 
                h.h3_index,
                h.lat,
                h.lon,
                ST_POINT(h.lon, h.lat) AS h3_point
            FROM 
                dev_geography_oja_ev_charger_features.h3_11 h
            JOIN 
                geography.neighborhoods n ON h.neighborhood_id = n.id AND h.country = n.country
            JOIN 
                geography.cities c ON n.city_id = c.id AND h.country = c.country
            WHERE 
                h.country = '{country}'
                AND {geographic_clause}
        ),
        nearest_h3_cells AS (
            SELECT 
                s.poi_id,
                s.supermarket_name,
                s.address,
                s.latitude,
                s.longitude,
                h.h3_index,
                ST_Distance(to_spherical_geography(s.poi_point), to_spherical_geography(h.h3_point)) as distance_meters,
                ROW_NUMBER() OVER (PARTITION BY s.poi_id ORDER BY ST_Distance(s.poi_point, h.h3_point)) AS rn
            FROM 
                selected_pois s
            CROSS JOIN 
                h3_cells h
            WHERE 
                ST_Distance(to_spherical_geography(s.poi_point), to_spherical_geography(h.h3_point)) < {poi_radius_meters}
        )
        SELECT 
            n.poi_id,
            n.supermarket_name,
            n.address,
            n.latitude,
            n.longitude,
            n.h3_index,
            n.distance_meters,
            p.*
        FROM 
            nearest_h3_cells n
        JOIN 
            dev_ev_connect_oja_ev_charger_features.station_selector_predictions_final_without_explanation p 
            ON n.h3_index = p.h3_index
        WHERE 
            n.rn = 1
            AND p.country = '{country}'
        ORDER BY 
            p.pred_rapid_score DESC,
            p.highways_and_major_roads_mean_aadt_within_1000_m DESC
        LIMIT 1000
    """
        return self.execute_query(query, "pipeline_data_v2")

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
