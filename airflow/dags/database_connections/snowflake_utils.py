from datetime import datetime, timedelta, timezone


def get_last_date_or_default(conn, table_fqname: str, column_name: str, default_date: str = "2023-06-25") -> str:
    """
    Extract the last date from a Snowflake table for incremental loading.

    Args:
        conn: Snowflake connection object
        table_fqname: Fully qualified table name (e.g., "DB_FIND_A_MOVIE.BRONZE_PMS.TABLE_NAME")
        column_name: Column name to use as the date column
        default_date: Default date string if table is empty (default: "2023-06-25")

    Returns:
        str: Date string in "YYYY-MM-DD" format
    """
    cursor = conn.cursor()
    try:
        query = f"SELECT MAX({column_name}) FROM {table_fqname}"
        cursor.execute(query)
        result = cursor.fetchone()
        if result and result[0]:
            return (result[0].strftime("%Y-%m-%d"))
        else:
            return default_date
    finally:
        cursor.close()


def get_latest_facility_ids(conn) -> list[int]:
    """
    Retrieve the latest distinct facility IDs from Snowflake based on the most recent EXTRACTED_AT.

    Args:
        conn: Snowflake connection object

    Returns:
        List of facility IDs (integers)
    """
    query = """
        SELECT ID
        FROM DB_FIND_A_MOVIE.BRONZE_PMS.BI_GET_STORAGE_FACILITY_LIST
        QUALIFY ROW_NUMBER() OVER (PARTITION BY ID ORDER BY EXTRACTED_AT DESC) = 1
    """
    with conn.cursor() as cur:
        cur.execute(query)
        results = cur.fetchall()
        facility_ids = [row[0] for row in results]
    return facility_ids


def get_last_modified_datetime_or_default(
    conn,
    table_fqname: str,
    column_name: str = "LAST_MODIFIED_DATETIME",
    default_datetime: str = "2023-01-01T00:00:00Z",
    overlap_minutes: int = 5
) -> str:
    """
    Retrieve the maximum lastModifiedDateTime from a Snowflake table for incremental loading,
    with a configurable overlap window to avoid missing edge-case records.

    Args:
        conn: Snowflake connection object
        table_fqname: Fully qualified table name (e.g., "DB_FIND_A_MOVIE.BRONZE_BC.TABLE_NAME")
        column_name: Column containing the lastModifiedDateTime timestamp
        default_datetime: Default ISO datetime string if table is empty (UTC)
        overlap_minutes: Minutes to subtract from max timestamp to create overlap window (default: 5)

    Returns:
        str: ISO 8601 formatted datetime string in UTC (e.g., "2024-01-15T10:30:00Z")

    Notes:
        - Applies overlap_minutes safety window to avoid missing records at boundary
        - Returns default_datetime if table is empty or has no records
        - Output format is compatible with Business Central API $filter OData query
    """
    cursor = conn.cursor()
    try:
        query = f"SELECT MAX({column_name}) FROM {table_fqname}"
        cursor.execute(query)
        result = cursor.fetchone()

        if result and result[0]:
            max_datetime = result[0]

            # If it's a datetime object, convert to UTC and subtract overlap
            if isinstance(max_datetime, datetime):
                # Ensure it's timezone-aware (assume UTC if naive)
                if max_datetime.tzinfo is None:
                    max_datetime = max_datetime.replace(tzinfo=timezone.utc)

                # Subtract overlap window
                watermark_datetime = max_datetime - timedelta(minutes=overlap_minutes)

                # Return in ISO 8601 format with 'Z' suffix
                return watermark_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

            # If it's already a string, try to parse and process
            elif isinstance(max_datetime, str):
                # Parse string to datetime
                parsed = datetime.fromisoformat(max_datetime.replace("Z", "+00:00"))
                watermark_datetime = parsed - timedelta(minutes=overlap_minutes)
                return watermark_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Return default if no data found
        print(f"[INFO] No existing data found in {table_fqname}. Using default: {default_datetime}")
        return default_datetime

    finally:
        cursor.close()


def parse_odata_datetime(dt_str: str) -> datetime:
    """
    Parse OData datetime string to Python datetime object.

    Handles formats:
    - 2024-01-15T10:30:00Z
    - 2024-01-15T10:30:00.123Z
    - 2024-01-15T10:30:00+00:00

    Args:
        dt_str: OData datetime string

    Returns:
        datetime: Python datetime object in UTC
    """
    if not dt_str:
        return None

    # Remove 'Z' and replace with '+00:00' for proper parsing
    dt_str_normalized = dt_str.replace("Z", "+00:00")

    try:
        return datetime.fromisoformat(dt_str_normalized)
    except ValueError:
        # Fallback: try parsing without timezone info
        dt_str_clean = dt_str.replace("Z", "")
        return datetime.fromisoformat(dt_str_clean).replace(tzinfo=timezone.utc)
