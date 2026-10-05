from services.database_service import DatabaseService

class CrimeModel:
    @classmethod
    def get_all(cls, filters=None, limit=None, offset=None):
        query = "SELECT * FROM crime_data WHERE 1=1"
        params = []

        if filters:
            state = str(filters.get("state", "")).strip()
            district = str(filters.get("district", "")).strip()
            area = str(filters.get("area", "")).strip()
            year = str(filters.get("year", "")).strip()
            crime_type = str(filters.get("crime_type", "")).strip()

            if state and state.lower() != "all":
                query += " AND state = %s"
                params.append(state)
            if district and district.lower() != "all":
                query += " AND district = %s"
                params.append(district)
            if area and area.lower() != "all":
                if filters.get("exact_area"):
                    query += " AND area = %s"
                    params.append(area)
                else:
                    query += " AND area LIKE %s"
                    params.append(f"%{area}%")
            if year and year.lower() != "all":
                try:
                    query += " AND year = %s"
                    params.append(int(year))
                except ValueError:
                    pass
            if crime_type and crime_type.lower() != "all":
                query += " AND crime_type = %s"
                params.append(crime_type)
            if filters.get("min_cases"):
                try:
                    query += " AND cases_reported >= %s"
                    params.append(int(filters["min_cases"]))
                except ValueError:
                    pass
            if filters.get("max_cases"):
                try:
                    query += " AND cases_reported <= %s"
                    params.append(int(filters["max_cases"]))
                except ValueError:
                    pass
            if filters.get("min_rate"):
                try:
                    query += " AND crime_rate_per_100k >= %s"
                    params.append(float(filters["min_rate"]))
                except ValueError:
                    pass
            if filters.get("max_rate"):
                try:
                    query += " AND crime_rate_per_100k <= %s"
                    params.append(float(filters["max_rate"]))
                except ValueError:
                    pass

        query += " ORDER BY year DESC, state ASC, district ASC, area ASC"

        if limit is not None:
            query += " LIMIT %s"
            params.append(int(limit))
            if offset is not None:
                query += " OFFSET %s"
                params.append(int(offset))

        return DatabaseService.execute_query(query, tuple(params))

    @classmethod
    def get_by_id(cls, record_id):
        return DatabaseService.execute_query(
            "SELECT * FROM crime_data WHERE id = %s", (record_id,), fetch_one=True
        )

    @classmethod
    def create(cls, state, district, area, year, crime_type, cases_reported, chargesheeted, convictions, population):
        pop = int(population)
        cases = int(cases_reported)
        crime_rate = round((cases / pop) * 100000, 2) if pop > 0 else 0.0

        query = """
        INSERT INTO crime_data 
        (state, district, area, year, crime_type, cases_reported, chargesheeted, convictions, population, crime_rate_per_100k)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            state.strip(), district.strip(), area.strip(), int(year),
            crime_type.strip(), cases, int(chargesheeted), int(convictions), pop, crime_rate
        )
        # Also ensure locations table has this entry
        try:
            DatabaseService.execute_query(
                "INSERT OR IGNORE INTO locations (state, district, area) VALUES (%s, %s, %s)",
                (state.strip(), district.strip(), area.strip()), fetch_all=False
            )
        except Exception:
            pass
        return DatabaseService.execute_insert(query, params)

    @classmethod
    def create_batch(cls, records_list):
        """High-speed batch insert for CSV imports and bulk loading."""
        if not records_list:
            return 0

        query = """
        INSERT INTO crime_data 
        (state, district, area, year, crime_type, cases_reported, chargesheeted, convictions, population, crime_rate_per_100k)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        rows = []
        locs = set()
        for r in records_list:
            pop = int(r.get('population', 100000))
            cases = int(r.get('cases_reported', 0))
            chg = int(r.get('chargesheeted', 0))
            conv = int(r.get('convictions', 0))
            rate = round((cases / pop) * 100000, 2) if pop > 0 else 0.0
            st = str(r.get('state', '')).strip()
            dist = str(r.get('district', '')).strip()
            ar = str(r.get('area', '')).strip()
            yr = int(r.get('year', 2024))
            ct = str(r.get('crime_type', '')).strip()

            rows.append((st, dist, ar, yr, ct, cases, chg, conv, pop, rate))
            if st and dist and ar:
                locs.add((st, dist, ar))

        count = DatabaseService.execute_batch(query, rows)

        # Batch insert distinct locations
        if locs:
            try:
                DatabaseService.execute_batch(
                    "INSERT OR IGNORE INTO locations (state, district, area) VALUES (%s, %s, %s)",
                    list(locs)
                )
            except Exception:
                pass

        return count

    @classmethod
    def update(cls, record_id, state, district, area, year, crime_type, cases_reported, chargesheeted, convictions, population):
        pop = int(population)
        cases = int(cases_reported)
        crime_rate = round((cases / pop) * 100000, 2) if pop > 0 else 0.0

        query = """
        UPDATE crime_data 
        SET state = %s, district = %s, area = %s, year = %s, crime_type = %s, 
            cases_reported = %s, chargesheeted = %s, convictions = %s, population = %s, crime_rate_per_100k = %s
        WHERE id = %s
        """
        params = (
            state.strip(), district.strip(), area.strip(), int(year),
            crime_type.strip(), cases, int(chargesheeted), int(convictions), pop, crime_rate, record_id
        )
        return DatabaseService.execute_query(query, params, fetch_all=False)

    @classmethod
    def delete(cls, record_id):
        return DatabaseService.execute_query(
            "DELETE FROM crime_data WHERE id = %s", (record_id,), fetch_all=False
        )

    # Cascading Dropdowns Helpers (Using Master Location Tables with Fallback)
    @classmethod
    def get_distinct_states(cls):
        try:
            rows = DatabaseService.execute_query("SELECT state_name FROM geo_states WHERE is_active = 1 ORDER BY state_name ASC")
            if rows:
                return [r["state_name"] for r in rows if r.get("state_name")]
        except Exception:
            pass
        rows = DatabaseService.execute_query("SELECT DISTINCT state FROM crime_data WHERE state IS NOT NULL AND state != '' ORDER BY state ASC")
        return [r["state"] for r in rows if r.get("state")]

    @classmethod
    def get_all_districts(cls):
        try:
            rows = DatabaseService.execute_query("SELECT DISTINCT district_name FROM geo_districts WHERE is_active = 1 ORDER BY district_name ASC")
            if rows:
                return [r["district_name"] for r in rows if r.get("district_name")]
        except Exception:
            pass
        rows = DatabaseService.execute_query("SELECT DISTINCT district FROM crime_data WHERE district IS NOT NULL AND district != '' ORDER BY district ASC")
        return [r["district"] for r in rows if r.get("district")]

    @classmethod
    def get_all_areas(cls):
        try:
            rows = DatabaseService.execute_query("SELECT DISTINCT area FROM locations WHERE is_active = 1 ORDER BY area ASC")
            if rows:
                return [r["area"] for r in rows if r.get("area")]
        except Exception:
            pass
        rows = DatabaseService.execute_query("SELECT DISTINCT area FROM crime_data WHERE area IS NOT NULL AND area != '' ORDER BY area ASC")
        return [r["area"] for r in rows if r.get("area")]

    @classmethod
    def get_districts_by_state(cls, state=None):
        state_clean = state.strip() if state and isinstance(state, str) else None
        if not state_clean or state_clean.lower() == 'all':
            return cls.get_all_districts()

        try:
            rows = DatabaseService.execute_query(
                "SELECT district_name FROM geo_districts WHERE state_name = %s AND is_active = 1 ORDER BY district_name ASC",
                (state_clean,)
            )
            if rows:
                return [r["district_name"] for r in rows if r.get("district_name")]
        except Exception:
            pass
        rows = DatabaseService.execute_query(
            "SELECT DISTINCT district FROM crime_data WHERE state = %s ORDER BY district ASC",
            (state_clean,)
        )
        return [r["district"] for r in rows if r.get("district")]

    @classmethod
    def get_areas_by_state(cls, state=None):
        """Return all distinct areas within a given state."""
        state_clean = state.strip() if state and isinstance(state, str) else None
        if not state_clean or state_clean.lower() == 'all':
            return cls.get_all_areas()

        try:
            rows = DatabaseService.execute_query(
                "SELECT DISTINCT area FROM locations WHERE state = %s AND is_active = 1 ORDER BY area ASC",
                (state_clean,)
            )
            if rows:
                return [r["area"] for r in rows if r.get("area")]
        except Exception:
            pass
        rows = DatabaseService.execute_query(
            "SELECT DISTINCT area FROM crime_data WHERE state = %s ORDER BY area ASC",
            (state_clean,)
        )
        return [r["area"] for r in rows if r.get("area")]

    @classmethod
    def get_areas_by_district(cls, district=None, state=None):
        """
        Return distinct areas filtered by State and/or District.
        - If both state and district are provided (and neither is 'all'): WHERE state = %s AND district = %s
        - If only district is provided (and not 'all'): WHERE district = %s
        - If only state is provided (and not 'all'): WHERE state = %s
        - If neither or both 'all': return all distinct areas
        """
        state_clean = state.strip() if state and isinstance(state, str) else None
        district_clean = district.strip() if district and isinstance(district, str) else None

        if state_clean and state_clean.lower() == 'all':
            state_clean = None
        if district_clean and district_clean.lower() == 'all':
            district_clean = None

        if state_clean and district_clean:
            try:
                rows = DatabaseService.execute_query(
                    "SELECT area FROM locations WHERE state = %s AND district = %s AND is_active = 1 ORDER BY area ASC",
                    (state_clean, district_clean)
                )
                if rows:
                    return [r["area"] for r in rows if r.get("area")]
            except Exception:
                pass
            rows = DatabaseService.execute_query(
                "SELECT DISTINCT area FROM crime_data WHERE state = %s AND district = %s ORDER BY area ASC",
                (state_clean, district_clean)
            )
            return [r["area"] for r in rows if r.get("area")]
        elif district_clean:
            try:
                rows = DatabaseService.execute_query(
                    "SELECT area FROM locations WHERE district = %s AND is_active = 1 ORDER BY area ASC",
                    (district_clean,)
                )
                if rows:
                    return [r["area"] for r in rows if r.get("area")]
            except Exception:
                pass
            rows = DatabaseService.execute_query(
                "SELECT DISTINCT area FROM crime_data WHERE district = %s ORDER BY area ASC",
                (district_clean,)
            )
            return [r["area"] for r in rows if r.get("area")]
        elif state_clean:
            return cls.get_areas_by_state(state_clean)
        else:
            return cls.get_all_areas()

    @classmethod
    def get_distinct_years(cls):
        rows = DatabaseService.execute_query("SELECT DISTINCT year FROM crime_data ORDER BY year DESC")
        return [r["year"] for r in rows if r.get("year")]

    @classmethod
    def get_distinct_crime_types(cls):
        rows = DatabaseService.execute_query("SELECT DISTINCT crime_type FROM crime_data ORDER BY crime_type ASC")
        return [r["crime_type"] for r in rows if r.get("crime_type")]

    # Statistics / Analytics Queries
    @classmethod
    def get_summary_stats(cls, filters=None):
        query = """
        SELECT 
            COUNT(DISTINCT state) as total_states,
            COUNT(DISTINCT district) as total_districts,
            COUNT(DISTINCT area) as total_areas,
            COUNT(DISTINCT crime_type) as total_crime_types,
            COUNT(DISTINCT year) as total_years,
            MIN(year) as min_year,
            MAX(year) as max_year,
            COUNT(*) as total_records,
            COALESCE(SUM(cases_reported), 0) as total_cases,
            COALESCE(SUM(chargesheeted), 0) as total_chargesheeted,
            COALESCE(SUM(convictions), 0) as total_convictions,
            COALESCE(AVG(crime_rate_per_100k), 0.0) as avg_crime_rate
        FROM crime_data WHERE 1=1
        """
        params = []
        if filters:
            state = str(filters.get("state", "")).strip()
            district = str(filters.get("district", "")).strip()
            area = str(filters.get("area", "")).strip()
            year = str(filters.get("year", "")).strip()
            crime_type = str(filters.get("crime_type", "")).strip()

            if state and state.lower() != "all":
                query += " AND state = %s"
                params.append(state)
            if district and district.lower() != "all":
                query += " AND district = %s"
                params.append(district)
            if area and area.lower() != "all":
                if filters.get("exact_area"):
                    query += " AND area = %s"
                    params.append(area)
                else:
                    query += " AND area LIKE %s"
                    params.append(f"%{area}%")
            if year and year.lower() != "all":
                try:
                    query += " AND year = %s"
                    params.append(int(year))
                except ValueError:
                    pass
            if crime_type and crime_type.lower() != "all":
                query += " AND crime_type = %s"
                params.append(crime_type)
            if filters.get("min_cases"):
                try:
                    query += " AND cases_reported >= %s"
                    params.append(int(filters["min_cases"]))
                except ValueError:
                    pass
            if filters.get("max_cases"):
                try:
                    query += " AND cases_reported <= %s"
                    params.append(int(filters["max_cases"]))
                except ValueError:
                    pass
            if filters.get("min_rate"):
                try:
                    query += " AND crime_rate_per_100k >= %s"
                    params.append(float(filters["min_rate"]))
                except ValueError:
                    pass
            if filters.get("max_rate"):
                try:
                    query += " AND crime_rate_per_100k <= %s"
                    params.append(float(filters["max_rate"]))
                except ValueError:
                    pass

        res = DatabaseService.execute_query(query, tuple(params), fetch_one=True) or {}
        tot_cases = res.get('total_cases', 0) or 0
        tot_chg = res.get('total_chargesheeted', 0) or 0
        tot_conv = res.get('total_convictions', 0) or 0
        res['chargesheet_rate'] = round((tot_chg / tot_cases * 100), 2) if tot_cases > 0 else 0.0
        res['conviction_rate'] = round((tot_conv / tot_chg * 100), 2) if tot_chg > 0 else 0.0
        return res

    @classmethod
    def get_top_crime_areas(cls, limit=10, filters=None):
        query = """
        SELECT area, district, state, SUM(cases_reported) as total_cases, 
               AVG(crime_rate_per_100k) as avg_crime_rate,
               SUM(chargesheeted) as total_chargesheeted,
               SUM(convictions) as total_convictions
        FROM crime_data WHERE 1=1
        """
        params = []
        if filters:
            state = str(filters.get("state", "")).strip()
            district = str(filters.get("district", "")).strip()
            area = str(filters.get("area", "")).strip()
            year = str(filters.get("year", "")).strip()

            if state and state.lower() != "all":
                query += " AND state = %s"
                params.append(state)
            if district and district.lower() != "all":
                query += " AND district = %s"
                params.append(district)
            if area and area.lower() != "all":
                query += " AND area LIKE %s"
                params.append(f"%{area}%")
            if year and year.lower() != "all":
                try:
                    query += " AND year = %s"
                    params.append(int(year))
                except ValueError:
                    pass
            crime_type = str(filters.get("crime_type", "")).strip()
            if crime_type and crime_type.lower() != "all":
                query += " AND crime_type = %s"
                params.append(crime_type)

        query += " GROUP BY area, district, state ORDER BY total_cases DESC LIMIT %s"
        params.append(limit)
        return DatabaseService.execute_query(query, tuple(params))
