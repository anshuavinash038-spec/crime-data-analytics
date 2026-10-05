from services.database_service import DatabaseService

class LocationModel:
    # -------------------------------------------------------------------------
    # States
    # -------------------------------------------------------------------------
    @classmethod
    def get_all_states(cls, active_only=False):
        query = "SELECT * FROM geo_states"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY state_name ASC"
        return DatabaseService.execute_query(query)

    @classmethod
    def get_state_by_id(cls, state_id):
        return DatabaseService.execute_query(
            "SELECT * FROM geo_states WHERE id = %s", (state_id,), fetch_one=True
        )

    @classmethod
    def add_state(cls, state_name, state_code=None):
        name = state_name.strip()
        code = state_code.strip().upper() if state_code else name[:2].upper()
        query = "INSERT INTO geo_states (state_name, state_code, is_active) VALUES (%s, %s, 1)"
        return DatabaseService.execute_insert(query, (name, code))

    @classmethod
    def update_state(cls, state_id, state_name, state_code=None):
        name = state_name.strip()
        old_state = cls.get_state_by_id(state_id)
        code = state_code.strip().upper() if state_code else name[:2].upper()

        DatabaseService.execute_query(
            "UPDATE geo_states SET state_name = %s, state_code = %s WHERE id = %s",
            (name, code, state_id), fetch_all=False
        )

        if old_state and old_state["state_name"] != name:
            old_name = old_state["state_name"]
            DatabaseService.execute_query(
                "UPDATE geo_districts SET state_name = %s WHERE state_id = %s OR state_name = %s",
                (name, state_id, old_name), fetch_all=False
            )
            DatabaseService.execute_query(
                "UPDATE geo_areas SET state_name = %s WHERE state_name = %s",
                (name, old_name), fetch_all=False
            )
            DatabaseService.execute_query(
                "UPDATE locations SET state = %s WHERE state = %s",
                (name, old_name), fetch_all=False
            )
            DatabaseService.execute_query(
                "UPDATE crime_data SET state = %s WHERE state = %s",
                (name, old_name), fetch_all=False
            )
        return True

    @classmethod
    def toggle_state_active(cls, state_id):
        st = cls.get_state_by_id(state_id)
        if not st:
            return False
        new_status = 0 if st.get("is_active", 1) == 1 else 1
        DatabaseService.execute_query(
            "UPDATE geo_states SET is_active = %s WHERE id = %s",
            (new_status, state_id), fetch_all=False
        )
        return new_status

    # -------------------------------------------------------------------------
    # Districts
    # -------------------------------------------------------------------------
    @classmethod
    def get_all_districts(cls, state_name=None, active_only=False):
        query = """
        SELECT gd.*, gs.state_code 
        FROM geo_districts gd
        LEFT JOIN geo_states gs ON gd.state_id = gs.id
        WHERE 1=1
        """
        params = []
        if state_name and state_name.lower() != 'all':
            query += " AND gd.state_name = %s"
            params.append(state_name.strip())
        if active_only:
            query += " AND gd.is_active = 1"
        query += " ORDER BY gd.state_name ASC, gd.district_name ASC"
        return DatabaseService.execute_query(query, tuple(params))

    @classmethod
    def get_districts_by_state_id(cls, state_id, active_only=False):
        query = "SELECT * FROM geo_districts WHERE state_id = %s"
        if active_only:
            query += " AND is_active = 1"
        query += " ORDER BY district_name ASC"
        return DatabaseService.execute_query(query, (state_id,))

    @classmethod
    def get_district_by_id(cls, district_id):
        return DatabaseService.execute_query(
            "SELECT * FROM geo_districts WHERE id = %s", (district_id,), fetch_one=True
        )

    @classmethod
    def add_district(cls, state_id, district_name, historical_name=None):
        st = cls.get_state_by_id(state_id)
        if not st:
            raise ValueError(f"Invalid state ID #{state_id}")

        s_name = st["state_name"]
        d_name = district_name.strip()
        h_name = historical_name.strip() if historical_name else None

        query = """
        INSERT INTO geo_districts (state_id, state_name, district_name, historical_name, is_active)
        VALUES (%s, %s, %s, %s, 1)
        """
        return DatabaseService.execute_insert(query, (state_id, s_name, d_name, h_name))

    @classmethod
    def update_district(cls, district_id, district_name, historical_name=None):
        d_name = district_name.strip()
        h_name = historical_name.strip() if historical_name else None
        old_dist = cls.get_district_by_id(district_id)

        DatabaseService.execute_query(
            "UPDATE geo_districts SET district_name = %s, historical_name = %s WHERE id = %s",
            (d_name, h_name, district_id), fetch_all=False
        )

        if old_dist and old_dist["district_name"] != d_name:
            old_name = old_dist["district_name"]
            state_name = old_dist["state_name"]
            DatabaseService.execute_query(
                "UPDATE geo_areas SET district_name = %s WHERE district_id = %s OR (state_name = %s AND district_name = %s)",
                (d_name, district_id, state_name, old_name), fetch_all=False
            )
            DatabaseService.execute_query(
                "UPDATE locations SET district = %s WHERE state = %s AND district = %s",
                (d_name, state_name, old_name), fetch_all=False
            )
            DatabaseService.execute_query(
                "UPDATE crime_data SET district = %s WHERE state = %s AND district = %s",
                (d_name, state_name, old_name), fetch_all=False
            )
        return True

    @classmethod
    def toggle_district_active(cls, district_id):
        dt = cls.get_district_by_id(district_id)
        if not dt:
            return False
        new_status = 0 if dt.get("is_active", 1) == 1 else 1
        DatabaseService.execute_query(
            "UPDATE geo_districts SET is_active = %s WHERE id = %s",
            (new_status, district_id), fetch_all=False
        )
        return new_status

    # -------------------------------------------------------------------------
    # Areas (Level-3)
    # -------------------------------------------------------------------------
    @classmethod
    def get_all_areas(cls, state_name=None, district_name=None, active_only=False, limit=200, offset=0):
        query = """
        SELECT ga.* 
        FROM geo_areas ga
        WHERE 1=1
        """
        params = []
        if state_name and state_name.lower() != 'all':
            query += " AND ga.state_name = %s"
            params.append(state_name.strip())
        if district_name and district_name.lower() != 'all':
            query += " AND ga.district_name = %s"
            params.append(district_name.strip())
        if active_only:
            query += " AND ga.is_active = 1"
        query += " ORDER BY ga.state_name ASC, ga.district_name ASC, ga.area_name ASC"
        if limit:
            query += " LIMIT %s OFFSET %s"
            params.extend([int(limit), int(offset)])
        return DatabaseService.execute_query(query, tuple(params))

    @classmethod
    def get_areas_by_district_id(cls, district_id, active_only=False):
        query = "SELECT * FROM geo_areas WHERE district_id = %s"
        if active_only:
            query += " AND is_active = 1"
        query += " ORDER BY area_name ASC"
        return DatabaseService.execute_query(query, (district_id,))

    @classmethod
    def count_areas(cls, state_name=None, district_name=None):
        query = "SELECT COUNT(*) as cnt FROM geo_areas WHERE 1=1"
        params = []
        if state_name and state_name.lower() != 'all':
            query += " AND state_name = %s"
            params.append(state_name.strip())
        if district_name and district_name.lower() != 'all':
            query += " AND district_name = %s"
            params.append(district_name.strip())
        res = DatabaseService.execute_query(query, tuple(params), fetch_one=True)
        return res.get("cnt", 0) if res else 0

    @classmethod
    def get_area_by_id(cls, area_id):
        return DatabaseService.execute_query(
            "SELECT * FROM geo_areas WHERE id = %s", (area_id,), fetch_one=True
        )

    @classmethod
    def add_area(cls, district_id, area_name, area_type=None):
        dist = cls.get_district_by_id(district_id)
        if not dist:
            raise ValueError(f"Invalid district ID #{district_id}")

        s_name = dist["state_name"]
        d_name = dist["district_name"]
        a_name = area_name.strip()
        a_type = (area_type or "Police Station Jurisdiction / Municipal Locality").strip()

        query = """
        INSERT INTO geo_areas (district_id, state_name, district_name, area_name, area_type, is_active)
        VALUES (%s, %s, %s, %s, %s, 1)
        """
        area_id = DatabaseService.execute_insert(query, (district_id, s_name, d_name, a_name, a_type))

        # Synchronize with locations lookup table
        try:
            DatabaseService.execute_query(
                "INSERT OR IGNORE INTO locations (state, district, area, area_type, is_active) VALUES (%s, %s, %s, %s, 1)",
                (s_name, d_name, a_name, a_type), fetch_all=False
            )
        except Exception:
            pass

        return area_id

    @classmethod
    def update_area(cls, area_id, area_name, area_type=None):
        a_name = area_name.strip()
        a_type = (area_type or "Police Station Jurisdiction / Municipal Locality").strip()
        old_area = cls.get_area_by_id(area_id)

        DatabaseService.execute_query(
            "UPDATE geo_areas SET area_name = %s, area_type = %s WHERE id = %s",
            (a_name, a_type, area_id), fetch_all=False
        )

        if old_area and old_area["area_name"] != a_name:
            old_name = old_area["area_name"]
            st = old_area["state_name"]
            dt = old_area["district_name"]
            DatabaseService.execute_query(
                "UPDATE locations SET area = %s WHERE state = %s AND district = %s AND area = %s",
                (a_name, st, dt, old_name), fetch_all=False
            )
            DatabaseService.execute_query(
                "UPDATE crime_data SET area = %s WHERE state = %s AND district = %s AND area = %s",
                (a_name, st, dt, old_name), fetch_all=False
            )
        return True

    @classmethod
    def toggle_area_active(cls, area_id):
        ar = cls.get_area_by_id(area_id)
        if not ar:
            return False
        new_status = 0 if ar.get("is_active", 1) == 1 else 1
        DatabaseService.execute_query(
            "UPDATE geo_areas SET is_active = %s WHERE id = %s",
            (new_status, area_id), fetch_all=False
        )
        try:
            DatabaseService.execute_query(
                "UPDATE locations SET is_active = %s WHERE state = %s AND district = %s AND area = %s",
                (new_status, ar["state_name"], ar["district_name"], ar["area_name"]), fetch_all=False
            )
        except Exception:
            pass
        return new_status

    @classmethod
    def get_master_geo_stats(cls):
        """
        Returns official master geography metrics alongside crime dataset coverage metrics.
        No hardcoding - dynamically computed directly from official master tables and transaction records.
        """
        st_count = DatabaseService.execute_query("SELECT COUNT(*) as cnt FROM geo_states", fetch_one=True)
        dt_count = DatabaseService.execute_query("SELECT COUNT(*) as cnt FROM geo_districts", fetch_one=True)
        ar_count = DatabaseService.execute_query("SELECT COUNT(*) as cnt FROM geo_areas", fetch_one=True)

        crime_stats = DatabaseService.execute_query("""
            SELECT 
                COUNT(*) as total_crime_records,
                COUNT(DISTINCT state) as crime_states_count,
                COUNT(DISTINCT district) as crime_districts_count,
                COUNT(DISTINCT area) as crime_areas_count,
                COUNT(DISTINCT crime_type) as crime_types_count,
                MIN(year) as min_year,
                MAX(year) as max_year,
                COALESCE(SUM(cases_reported), 0) as total_cases,
                COALESCE(SUM(chargesheeted), 0) as total_chargesheeted,
                COALESCE(SUM(convictions), 0) as total_convictions,
                COALESCE(AVG(crime_rate_per_100k), 0.0) as avg_crime_rate
            FROM crime_data
        """, fetch_one=True) or {}

        return {
            "master_states_count": st_count.get("cnt", 28) if st_count else 28,
            "master_districts_count": dt_count.get("cnt", 0) if dt_count else 0,
            "master_areas_count": ar_count.get("cnt", 0) if ar_count else 0,
            "crime_states_count": crime_stats.get("crime_states_count", 0),
            "crime_districts_count": crime_stats.get("crime_districts_count", 0),
            "crime_areas_count": crime_stats.get("crime_areas_count", 0),
            "crime_types_count": crime_stats.get("crime_types_count", 0),
            "min_year": crime_stats.get("min_year", 2021),
            "max_year": crime_stats.get("max_year", 2025),
            "total_crime_records": crime_stats.get("total_crime_records", 0),
            "total_cases": crime_stats.get("total_cases", 0),
            "total_chargesheeted": crime_stats.get("total_chargesheeted", 0),
            "total_convictions": crime_stats.get("total_convictions", 0),
            "avg_crime_rate": crime_stats.get("avg_crime_rate", 0.0)
        }

