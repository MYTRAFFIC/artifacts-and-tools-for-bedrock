DOC = """
- Table Documentation
    - "pois"."enriched_pois" Table
        General Description
        The enriched_pois table in the pois database contains detailed information about Points of Interest (POIs) across several European countries. This table stores various characteristics of places such as restaurants, shops, services, public transportation, and other establishments.

        Table Structure
        Main Columns

        poi_id (string): Unique identifier for the point of interest
        source_id (string): Source data identifier
        title (string): Name of the point of interest
        latitude (double): Geographic coordinate - latitude
        longitude (double): Geographic coordinate - longitude
        address (string): Complete address of the POI
        link (string): URL of the website associated with the POI
        rating (double): Average rating given to the POI (scale varies by source)
        reviews (bigint): Number of reviews/comments
        phone (string): Phone number
        category (string): Main category of the POI (in "pois"."category_matrix" this column is named category_3, it's the most granular category). Should be used to filter pois based on category
        all_categories (array<string>): List of all categories associated with the POI
        price_parsed (bigint): Price level (typically on a scale of 1 to 4)
        ingestion_datetime (timestamp): Date and time of data ingestion
        ingestion_keywords (array<string>): Keywords associated with ingestion
        neighborhood_id (string): Identifier of the neighborhood where the POI is located
        ingestion_id (string): Identifier of the ingestion process
        brand_name (string): Brand/chain name
        brand_uuid (string): Unique brand identifier
        attributes (string): Additional attributes in JSON format
        inferred_main_category (string): Inferred main category
        category_id (string): Category identifier
        
        Partition
        country (string): Country code in ISO format (BE, DE, FR, ES, IT, GB, NL)
        
    - "pois"."category_matrix" Table
        General Description
        The category_matrix table in the pois database provides a hierarchical categorization system for Points of Interest. It establishes relationships between different category levels, allowing for classification of POIs into primary, secondary, and tertiary categories.
        Very small dataset
        
        Table Structure
        Main Columns

        category_1 (string): Primary category classification
        category_2 (string): Secondary category classification
        category_3 (string): Tertiary category classification
        
        Partition
        None
        
    - "pipeline_data_v2"."average_vehicle_flow_by_day" Table
        General Description
        The average_vehicle_flow_by_day table in the pipeline_data_v2 database contains traffic flow data for road segments. It provides information about vehicle traffic volumes on specific road segments over defined time periods. Most recent year to use for BE and NL 2023-01-01 for ES, FR, GB, IT, DE 2022-01-01

        Table Structure
        Main Columns

        road_segment_id (string): Unique identifier for the road segment
        forward (boolean): Direction of traffic flow (true for forward direction, false for reverse)
        start_week (string): Start date of the measurement period
        end_week (string): End date of the measurement period
        nb_unique_ids (bigint): Number of unique vehicle identifiers recorded
        unscaled_average_daily_traffic (double): Raw average daily traffic count
        average_daily_traffic (double): Scaled/adjusted average daily traffic count (AADT)
        
        Partition
        year (string): Year of data collection
        country (string): Country code in ISO format
        provider (string): Data provider identifier
        flow_kind (string): Type of traffic flow measurement
        
    - "geography"."adjustment_zones" Table
        General Description
        The adjustment_zones table in the geography database defines larger geographical areas used for data normalization and adjustment. These zones represent the highest level in the geographical hierarchy and contain multiple cities.

        Table Structure
        Main Columns

        id (string): Unique identifier for the adjustment zone
        name (string): Name of the adjustment zone
        area (string): Size of the area in square meters/kilometers
        geometry_4326 (string): WKT (Well-Known Text) representation of the zone's geometry in WGS84 coordinates
        
        Partition
        country (string): Country code in ISO format
        
    - "geography"."neighborhoods" Table
        General Description
        The neighborhoods table in the geography database contains detailed information about neighborhood-level geographical areas. Neighborhoods are smaller subdivisions within cities and represent the most granular level of geographical data.

        Table Structure
        Main Columns

        id (string): Unique identifier for the neighborhood
        local_code (string): Local administrative code for the neighborhood
        name (string): Name of the neighborhood
        city_id (string): Reference to the city containing this neighborhood
        area (string): Size of the area in square meters/kilometers
        geometry_4326 (string): WKT representation of the neighborhood's geometry in WGS84 coordinates
        tourist_flow_zone_id (string): Reference to a tourist flow zone if applicable
        
        Partition
        country (string): Country code in ISO format
        
    - "geography"."cities" Table
        General Description
        The cities table in the geography database contains information about city-level geographical areas. Cities are administrative units that contain multiple neighborhoods and are themselves contained within adjustment zones.

        Table Structure
        Main Columns

        id (string): Unique identifier for the city
        local_code (string): Local administrative code for the city
        name (string): Name of the city
        adjustment_zone_id (string): Reference to the adjustment zone containing this city
        area (string): Size of the area in square meters/kilometers
        geometry_4326 (string): WKT representation of the city's geometry in WGS84 coordinates
        
        Partition
        country (string): Country code in ISO format
        
    - "dev_ev_connect_oja_ev_charger_features"."station_selector_predictions_final_without_explanation" Table
        General Description
        The station_selector_predictions_final_without_explanation table in the dev_ev_connect_oja_ev_charger_features database contains prediction data for electric vehicle charging station placement. It includes various features and prediction scores for different types of charging stations at specific locations.

        Table Structure
        Main Columns

        h3_index (bigint): Hierarchical geospatial indexing identifier
        h3_resolution (int): Resolution level of the H3 index
        neighborhood_id (string): Reference to the neighborhood
        highways_and_major_roads_mean_aadt_within_100_m (double): Average Annual Daily Traffic on highways within 100m
        highways_and_major_roads_mean_aadt_within_1000_m (double): Average Annual Daily Traffic on highways within 1000m
        primary_roads_mean_aadt_within_100_m (double): Average Annual Daily Traffic on primary roads within 100m
        primary_roads_mean_aadt_within_1000_m (double): Average Annual Daily Traffic on primary roads within 1000m
        secondary_and_tertiary_roads_mean_aadt_within_100_m (double): Average Annual Daily Traffic on secondary roads within 100m
        secondary_and_tertiary_roads_mean_aadt_within_1000_m (double): Average Annual Daily Traffic on secondary roads within 1000m
        local_and_residential_roads_mean_aadt_within_100_m (double): Average Annual Daily Traffic on local roads within 100m
        local_and_residential_roads_mean_aadt_within_1000_m (double): Average Annual Daily Traffic on local roads within 1000m
        mean_aadt_over_3_nearest_roads (double): Average Annual Daily Traffic over 3 nearest roads
        mean_aadt_over_5_nearest_roads (double): Average Annual Daily Traffic over 5 nearest roads
        avg_ratio_aadt_weekend_weekday (double): Ratio of weekend to weekday traffic
        avg_vehicle_traffic_peak_hour (double): Average vehicle traffic during peak hours
        mean_average_duration_seconds (double): Mean duration of vehicle stops in seconds
        population_density_habitants_per_km2 (double): Population density per square kilometer
        households_in_income_quintile_4_5 (bigint): Number of households in the top two income quintiles
        purchasing_power_per_capita (double): Purchasing power per capita
        electric_vehicle_count (bigint): Count of electric vehicles in the area
        electric_vehicle_count_per_km2 (double): Density of electric vehicles per square kilometer
        ev_adoption_rate (double): Rate of electric vehicle adoption
        population_density_origin (double): Population density at origin points
        purchasing_power_per_capita_origin (double): Purchasing power per capita at origin points
        ev_adoption_rate_origin (double): Electric vehicle adoption rate at origin points
        electric_vehicle_count_origin (double): Count of electric vehicles at origin points
        nb_charging_stations_within_500_m (bigint): Number of existing charging stations within 500m
        polygons_within_500_m_average_daily_flow (double): Average daily flow within 500m polygons
        polygons_within_500_m_average_dwell_time_seconds (double): Average dwell time in seconds within 500m polygons
        is_fast_food_pois_within_100_m (int): Presence of fast food POIs within 100m (0/1)
        is_fuel_charging_and_service_areas_pois_within_100_m (int): Presence of fuel/service areas within 100m (0/1)
        is_general_markets_pois_within_100_m (int): Presence of general markets within 100m (0/1)
        is_health_places_pois_within_100_m (int): Presence of health places within 100m (0/1)
        is_industry_pois_within_100_m (int): Presence of industrial POIs within 100m (0/1)
        is_offices_building_pois_within_100_m (int): Presence of office buildings within 100m (0/1)
        is_public_services_pois_within_100_m (int): Presence of public services within 100m (0/1)
        is_shopping_centre_pois_within_100_m (int): Presence of shopping centers within 100m (0/1)
        is_tourist_accomodation_pois_within_100_m (int): Presence of tourist accommodations within 100m (0/1)
        is_transit_stop_pois_within_100_m (int): Presence of transit stops within 100m (0/1)
        pred_rapid (double): Prediction score for rapid charging station
        pred_fast (double): Prediction score for fast charging station
        pred_medium (double): Prediction score for medium charging station
        pred_slow (double): Prediction score for slow charging station
        pred_rapid_score (double): Normalized prediction score for rapid charging
        pred_fast_score (double): Normalized prediction score for fast charging
        pred_medium_score (double): Normalized prediction score for medium charging
        pred_slow_score (double): Normalized prediction score for slow charging
        
        Partition
        country (string): Country code in ISO format
        
    - "dev_geography_oja_ev_charger_features"."h3_11" Table
        General Description
        The h3_11 table in the dev_geography_oja_ev_charger_features database provides a mapping between H3 geospatial indices and geographical features. It links hexagonal H3 cells at resolution 11 to neighborhoods and road segments, enabling spatial analysis at a high resolution.

        Table Structure
        Main Columns

        h3_index (bigint): Hierarchical geospatial indexing identifier
        neighborhood_id (string): Reference to the neighborhood containing this H3 cell
        resolution (int): Resolution level of the H3 index (typically 11 for this table)
        lat (double): Latitude of the H3 cell center
        lon (double): Longitude of the H3 cell center
        road_segment_id (string): Reference to a road segment associated with this H3 cell
        geometry_4326 (string): WKT representation of the H3 cell's geometry in WGS84 coordinates
        
        Partition
        country (string): Country code in ISO format

- Table Relationships
	- POI-Geography Hierarchy: pois.enriched_pois → geography.neighborhoods (via neighborhood_id) → geography.cities → geography.adjustment_zones
	- POI-Category Mapping: pois.enriched_pois (category) ↔ pois.category_matrix (category_3) BE CAREFUL : always use lower(category) to make comparison to avoid errors
	- Traffic-POI Analysis:`pipeline_data_v2.average_vehicle_flow_by_day` (road_segment_id) ↔ `dev_geography_oja_ev_charger_features.h3_11` ↔ `pois.enriched_pois` (spatial proximity)
	- EV Charger Predictions - POI analysis: `dev_ev_connect_oja_ev_charger_features.station_selector_predictions_final_without_explanation` ↔ `h3_11` (h3_index) ↔ `pois.enriched_pois` (spatial proximity)

- Tips
	- When you need to filter on a category in POI database, don’t hesitate to query all "pois"."category_matrix" (it’s a very small table) it will give you a better understanding of what category to choose, verify also with the user if this category is what he is expecting
    - Spatial joins are important to link pois with EV charger predictions. Each POI should be associated to one h3_index.
    - Please avoid at all costs doing geographical queries on a column with "%[keyword]%": the risk of false positives is too high (ex %Paris% may contain many places in France not close at all to Paris)
    - In cities : Lyon, Marseille, Paris are divided in multiple rows, each row is part of the city like Paris 01, 02 etc.. be aware of this when trying to find a city
"""
