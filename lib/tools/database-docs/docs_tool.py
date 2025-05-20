from typing import Dict, List


class DatabaseDocumentationTool:
    """
    Tool to provide documentation about available databases, tables, and their relationships
    to help LLMs make better decisions about which queries to execute.
    """

    def __init__(self):
        """Initialize the documentation tool with predefined metadata about databases and tables"""
        # This would ideally be loaded from a configuration file or database
        self.database_docs = self._load_database_documentation()

    def _load_database_documentation(self) -> Dict:
        """Load documentation about databases and tables from a predefined structure

        In a production environment, this could be loaded from:
        - A JSON/YAML file in S3
        - A documentation table in DynamoDB
        - Generated dynamically from data catalogs
        """
        return {
            "databases": {
                "pipeline_data_v2": {
                    "description": "Contains pipeline processed data including vehicle flow statistics",
                    "tables": {
                        "average_vehicle_flow_by_day": {
                            "description": "Daily vehicle flow data aggregated by various dimensions",
                            "detailed_description": """
                                The average_vehicle_flow_by_day table in the pipeline_data_v2 database contains traffic flow data for road segments. 
                                It provides information about vehicle traffic volumes on specific road segments over defined time periods.
                            """,
                            "key_columns": [
                                "road_segment_id",
                                "forward",
                                "start_week",
                                "end_week",
                                "nb_unique_ids",
                                "unscaled_average_daily_traffic",
                                "average_daily_traffic",
                            ],
                            "partition_columns": [
                                "year",
                                "country",
                                "provider",
                                "flow_kind",
                            ],
                            "important_metrics": [
                                "adjusted_vehicle_count",
                                "average_daily_traffic",
                            ],
                            "partitioned_by": ["day", "country"],
                            "example_query": """
                                SELECT neighborhood_id, AVG(adjusted_vehicle_count) as avg_flow
                                FROM pipeline_data_v2.average_vehicle_flow_by_day 
                                WHERE country = 'FR' AND day >= '2024-01-01'
                                GROUP BY neighborhood_id
                                ORDER BY avg_flow DESC
                                LIMIT 10
                            """,
                            "notes": "Use average_daily_traffic for vehicle traffic metric",
                        },
                        "polygon_hierarchy": {
                            "description": "Defines the hierarchical relationships between geographical entities",
                            "key_columns": [
                                "child_id",
                                "parent_id",
                                "child_type",
                                "parent_type",
                                "country",
                            ],
                            "important_relationships": [
                                "neighborhood -> city -> adjustment_zone"
                            ],
                            "example_query": """
                                SELECT child_id, parent_id
                                FROM pipeline_data_v2.polygon_hierarchy
                                WHERE child_type = 'neighborhood' AND parent_type = 'city'
                                AND parent_id IN (SELECT id FROM geography.cities WHERE name LIKE '%Paris%')
                            """,
                        },
                    },
                },
                "geography": {
                    "description": "Contains geographical definitions and boundaries",
                    "tables": {
                        "adjustment_zones": {
                            "description": "Largest geographical division containing cities",
                            "detailed_description": """
                                The adjustment_zones table in the geography database defines larger geographical areas used for data normalization and adjustment. 
                                These zones represent the highest level in the geographical hierarchy and contain multiple cities.
                            """,
                            "key_columns": ["id", "name", "area", "geometry_4326"],
                            "partition_columns": ["country"],
                            "example_query": """
                                SELECT id, name, country
                                FROM geography.adjustment_zones
                                WHERE country = 'FR'
                            """,
                        },
                        "cities": {
                            "description": "City boundaries containing neighborhoods",
                            "detailed_description": """
                                The cities table in the geography database contains information about city-level geographical areas. 
                                Cities are administrative units that contain multiple neighborhoods and are themselves contained within adjustment zones.
                            """,
                            "key_columns": [
                                "id",
                                "local_code",
                                "name",
                                "adjustment_zone_id",
                                "area",
                                "geometry_4326",
                            ],
                            "partition_columns": ["country"],
                            "example_query": """
                                SELECT id, name 
                                FROM geography.cities
                                WHERE name LIKE '%Paris%' AND country = 'FR'
                            """,
                        },
                        "neighborhoods": {
                            "description": "Neighborhood boundaries, useful for local analysis",
                            "detailed_description": """
                                The neighborhoods table in the geography database contains detailed information about neighborhood-level geographical areas. 
                                Neighborhoods are smaller subdivisions within cities and represent the most granular level of geographical data.
                            """,
                            "key_columns": [
                                "id",
                                "local_code",
                                "name",
                                "city_id",
                                "area",
                                "geometry_4326",
                                "tourist_flow_zone_id",
                            ],
                            "partition_columns": ["country"],
                            "example_query": """
                                SELECT n.id, n.name
                                FROM geography.neighborhoods n
                                JOIN geography.cities c ON n.city_id = c.id
                                WHERE c.name LIKE '%Paris%' AND n.country = 'FR'
                            """,
                        },
                    },
                },
                "pois": {
                    "description": "Points of Interest data including businesses and landmarks",
                    "tables": {
                        "enriched_pois": {
                            "description": "Enriched POI data with categories and locations",
                            "detailed_description": """
                                The enriched_pois table in the pois database contains detailed information about Points of Interest (POIs) across several European countries. 
                                This table stores various characteristics of places such as restaurants, shops, services, public transportation, and other establishments.
                            """,
                            "key_columns": [
                                "poi_id",
                                "source_id",
                                "title",
                                "latitude",
                                "longitude",
                                "address",
                                "link",
                                "rating",
                                "reviews",
                                "phone",
                                "category",
                                "all_categories",
                                "price_parsed",
                                "ingestion_datetime",
                                "ingestion_keywords",
                                "neighborhood_id",
                                "ingestion_id",
                                "brand_name",
                                "brand_uuid",
                                "attributes",
                                "inferred_main_category",
                                "category_id",
                            ],
                            "partition_columns": ["country"],
                            "notes": "Column 'category' should be used to filter POIs based on category. Corresponds to category_3 in category_matrix table.",
                            "example_query": """
                                SELECT id, name, categories
                                FROM pois.enriched_pois
                                WHERE country = 'FR' AND categories LIKE '%supermarket%'
                            """,
                        },
                        "category_matrix": {
                            "description": "Matrix defining relationships between POI categories",
                            "detailed_description": """
                                The category_matrix table in the pois database provides a hierarchical categorization system for Points of Interest. 
                                It establishes relationships between different category levels, allowing for classification of POIs into primary, secondary, and tertiary categories.
                                This is a small dataset with no partitions.
                            """,
                            "key_columns": ["category_1", "category_2", "category_3"],
                            "notes": "category_3 is the most granular category and corresponds to the 'category' column in enriched_pois table.",
                            "example_query": """
                                SELECT category_id, category_name
                                FROM pois.category_matrix
                                WHERE category_name LIKE '%supermarket%' OR category_name LIKE '%grocery%'
                            """,
                        },
                    },
                },
                "dev_ev_connect_oja_ev_charger_features": {
                    "description": "EV charging station data and predictions",
                    "tables": {
                        "station_selector_predictions_final_without_explanation": {
                            "description": "Predictions for optimal EV charging station locations",
                            "detailed_description": """
                                The station_selector_predictions_final_without_explanation table in the dev_ev_connect_oja_ev_charger_features database 
                                contains prediction data for electric vehicle charging station placement. It includes various features and prediction scores 
                                for different types of charging stations at specific locations.
                            """,
                            "key_columns": [
                                "h3_index",
                                "h3_resolution",
                                "neighborhood_id",
                                "highways_and_major_roads_mean_aadt_within_100_m",
                                "highways_and_major_roads_mean_aadt_within_1000_m",
                                "primary_roads_mean_aadt_within_100_m",
                                "primary_roads_mean_aadt_within_1000_m",
                                "secondary_and_tertiary_roads_mean_aadt_within_100_m",
                                "secondary_and_tertiary_roads_mean_aadt_within_1000_m",
                                "local_and_residential_roads_mean_aadt_within_100_m",
                                "local_and_residential_roads_mean_aadt_within_1000_m",
                                "mean_aadt_over_3_nearest_roads",
                                "mean_aadt_over_5_nearest_roads",
                                "avg_ratio_aadt_weekend_weekday",
                                "avg_vehicle_traffic_peak_hour",
                                "mean_average_duration_seconds",
                                "population_density_habitants_per_km2",
                                "households_in_income_quintile_4_5",
                                "purchasing_power_per_capita",
                                "electric_vehicle_count",
                                "electric_vehicle_count_per_km2",
                                "ev_adoption_rate",
                                "population_density_origin",
                                "purchasing_power_per_capita_origin",
                                "ev_adoption_rate_origin",
                                "electric_vehicle_count_origin",
                                "nb_charging_stations_within_500_m",
                                "polygons_within_500_m_average_daily_flow",
                                "polygons_within_500_m_average_dwell_time_seconds",
                                "is_fast_food_pois_within_100_m",
                                "is_fuel_charging_and_service_areas_pois_within_100_m",
                                "is_general_markets_pois_within_100_m",
                                "is_health_places_pois_within_100_m",
                                "is_industry_pois_within_100_m",
                                "is_offices_building_pois_within_100_m",
                                "is_public_services_pois_within_100_m",
                                "is_shopping_centre_pois_within_100_m",
                                "is_tourist_accomodation_pois_within_100_m",
                                "is_transit_stop_pois_within_100_m",
                                "pred_rapid",
                                "pred_fast",
                                "pred_medium",
                                "pred_slow",
                                "pred_rapid_score",
                                "pred_fast_score",
                                "pred_medium_score",
                                "pred_slow_score",
                                "can_be_shown_rapid",
                                "can_be_shown_fast",
                                "can_be_shown_medium",
                                "can_be_shown_slow",
                                "latitude",
                                "longitude",
                            ],
                            "partition_columns": ["country"],
                            "prediction_columns": [
                                "pred_rapid_score",
                                "pred_fast_score",
                                "pred_medium_score",
                                "pred_slow_score",
                            ],
                            "example_query": """
                                SELECT location_id, prediction_score, latitude, longitude
                                FROM dev_ev_connect_oja_ev_charger_features.station_selector_predictions_final_without_explanation
                                WHERE country = 'FR'
                                ORDER BY prediction_score DESC
                                LIMIT 20
                            """,
                        }
                    },
                },
                "dev_geography_oja_ev_charger_features": {
                    "description": "H3 geographical indexing for EV charger analysis",
                    "tables": {
                        "h3_11": {
                            "description": "H3 level 11 hexagons with geographical features",
                            "detailed_description": """
                                The h3_11 table in the dev_geography_oja_ev_charger_features database provides a mapping between H3 geospatial indices and geographical features. 
                                It links hexagonal H3 cells at resolution 11 to neighborhoods and road segments, enabling spatial analysis at a high resolution.
                            """,
                            "key_columns": [
                                "h3_index",
                                "neighborhood_id",
                                "resolution",
                                "lat",
                                "lon",
                                "road_segment_id",
                                "geometry_4326",
                            ],
                            "partition_columns": ["country"],
                            "example_query": """
                                SELECT h3_index, neighborhood_id, features
                                FROM dev_geography_oja_ev_charger_features.h3_11
                                WHERE country = 'FR'
                                LIMIT 10
                            """,
                        }
                    },
                },
            },
            "common_joins": [
                {
                    "description": "Join neighborhoods with vehicle flow data",
                    "query": """
                        SELECT n.name as neighborhood_name, AVG(f.adjusted_vehicle_count) as avg_flow
                        FROM geography.neighborhoods n
                        JOIN pipeline_data_v2.average_vehicle_flow_by_day f ON n.id = f.neighborhood_id
                        WHERE n.country = 'FR' AND f.country = 'FR'
                        GROUP BY n.name
                        ORDER BY avg_flow DESC
                        LIMIT 10
                    """,
                },
                {
                    "description": "Find POIs near neighborhoods with high vehicle flow",
                    "query": """
                        SELECT p.name as poi_name, p.categories, AVG(f.adjusted_vehicle_count) as avg_flow
                        FROM pois.enriched_pois p
                        JOIN geography.neighborhoods n ON 
                            ST_DWithin(ST_Point(p.longitude, p.latitude), n.geometry_4326, 1000)
                        JOIN pipeline_data_v2.average_vehicle_flow_by_day f ON n.id = f.neighborhood_id
                        WHERE p.country = 'FR' AND n.country = 'FR' AND f.country = 'FR'
                            AND p.categories LIKE '%supermarket%'
                        GROUP BY p.name, p.categories
                        ORDER BY avg_flow DESC
                        LIMIT 20
                    """,
                },
                {
                    "description": "Join EV station predictions with nearby POIs",
                    "query": """
                        SELECT s.location_id, s.prediction_score, 
                            p.name as poi_name, p.categories,
                            ST_Distance(ST_Point(s.longitude, s.latitude), ST_Point(p.longitude, p.latitude)) as distance_meters
                        FROM dev_ev_connect_oja_ev_charger_features.station_selector_predictions_final_without_explanation s
                        JOIN pois.enriched_pois p ON 
                            ST_DWithin(ST_Point(s.longitude, s.latitude), ST_Point(p.longitude, p.latitude), 1000)
                        WHERE s.country = 'FR' AND p.country = 'FR'
                            AND p.categories LIKE '%supermarket%'
                        ORDER BY s.prediction_score DESC, distance_meters ASC
                        LIMIT 20
                    """,
                },
            ],
        }

    def get_database_overview(self) -> Dict:
        """Get overview of all available databases"""
        overview = {}
        for db_name, db_info in self.database_docs["databases"].items():
            overview[db_name] = {
                "description": db_info["description"],
                "tables": list(db_info["tables"].keys()),
            }
        return overview

    def get_database_info(self, database: str) -> Dict:
        """Get detailed information about a specific database"""
        if database in self.database_docs["databases"]:
            return self.database_docs["databases"][database]
        return {"error": f"Database '{database}' not found in documentation"}

    def get_table_info(self, database: str, table: str) -> Dict:
        """Get detailed information about a specific table"""
        if database in self.database_docs["databases"]:
            if table in self.database_docs["databases"][database]["tables"]:
                return self.database_docs["databases"][database]["tables"][table]
        return {"error": f"Table '{table}' not found in database '{database}'"}

    def search_tables(self, keyword: str) -> List[Dict]:
        """Search for tables containing a specific keyword in their metadata"""
        results = []
        for db_name, db_info in self.database_docs["databases"].items():
            for table_name, table_info in db_info["tables"].items():
                # Search in table name and description
                if (
                    keyword.lower() in table_name.lower()
                    or keyword.lower() in table_info["description"].lower()
                ):
                    results.append(
                        {
                            "database": db_name,
                            "table": table_name,
                            "description": table_info["description"],
                        }
                    )
        return results

    def get_common_joins(self) -> List[Dict]:
        """Get common join patterns between tables"""
        return self.database_docs["common_joins"]
