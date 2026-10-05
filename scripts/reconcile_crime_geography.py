# scripts/reconcile_crime_geography.py
"""
Reconciliation script to ensure 100% of crime_data rows reference valid entities in locations/geo_areas.
"""

import sqlite3

def reconcile():
    conn = sqlite3.connect("database/crime_analytics.db")
    cur = conn.cursor()

    print("--- Reconciling Crime Data Geography with Master LGD ---")

    # Mappings for known reorganizations / name disambiguations:
    # Format: (old_state, old_dist, old_area) -> (new_state, new_dist, new_area)
    mappings = {
        ("Arunachal Pradesh", "Lower Subansiri", "Kamporijo"): ("Arunachal Pradesh", "Kamle", "Kamporijo"),
        ("Chhattisgarh", "Rajnandgaon", "Chhuikhadan"): ("Chhattisgarh", "Khairagarh-Chhuikhadan-Gandai", "Chhuikhadan"),
        ("Chhattisgarh", "Rajnandgaon", "Khairagarh"): ("Chhattisgarh", "Khairagarh-Chhuikhadan-Gandai", "Khairagarh"),
        ("Goa", "South Goa", "Ponda"): ("Goa", "North Goa", "Ponda"),
        ("Gujarat", "Bhavnagar", "Mahuva"): ("Gujarat", "Bhavnagar", "Mahuva Bhavnagar"),
        ("Gujarat", "Junagadh", "Mangrol"): ("Gujarat", "Junagadh", "Mangrol Junagadh"),
        ("Gujarat", "Rajkot", "Jetpur"): ("Gujarat", "Rajkot", "Jetpur Rajkot"),
        ("Gujarat", "Surat", "Mandvi"): ("Gujarat", "Surat", "Mandvi Surat"),
        ("Gujarat", "Vadodara", "Waghodia"): ("Gujarat", "Vadodara", "Vaghodia"),
        ("Haryana", "Ambala", "Ambala"): ("Haryana", "Ambala", "Ambala City"),
        ("Haryana", "Hisar", "Barwala"): ("Haryana", "Hisar", "Barwala Hisar"),
        ("Himachal Pradesh", "Mandi", "Mandi Sadar"): ("Himachal Pradesh", "Mandi", "Mandi"),
        ("Jharkhand", "East Singhbhum", "Bahragora"): ("Jharkhand", "East Singhbhum", "Baharagora"),
        ("Jharkhand", "Palamu", "Chhatarpur"): ("Jharkhand", "Palamu", "Chhatarpur Palamu"),
        ("Karnataka", "Bengaluru Rural", "Doddaballapur"): ("Karnataka", "Bengaluru Rural", "Doddaballapura"),
        ("Karnataka", "Bengaluru Urban", "Anekal"): ("Karnataka", "Bengaluru Urban", "Anekal"),
        ("Karnataka", "Mysuru", "T. Narsipur"): ("Karnataka", "Mysuru", "T. Narasipura"),
        ("Kerala", "Kollam", "Karunagapally"): ("Kerala", "Kollam", "Karunagappally"),
        ("Madhya Pradesh", "Hoshangabad", "Itarsi"): ("Madhya Pradesh", "Hoshangabad (Narmadapuram)", "Itarsi"),
        ("Madhya Pradesh", "Hoshangabad", "Pipariya"): ("Madhya Pradesh", "Hoshangabad (Narmadapuram)", "Pipariya"),
        ("Madhya Pradesh", "Hoshangabad", "Sohagpur"): ("Madhya Pradesh", "Hoshangabad (Narmadapuram)", "Sohagpur"),
        ("Madhya Pradesh", "Hoshangabad", "Babai"): ("Madhya Pradesh", "Hoshangabad (Narmadapuram)", "Babai Makhan Nagar"),
        ("Madhya Pradesh", "Hoshangabad", "Seoni Malwa"): ("Madhya Pradesh", "Hoshangabad (Narmadapuram)", "Seoni Malwa"),
        ("Madhya Pradesh", "Hoshangabad", "Hoshangabad"): ("Madhya Pradesh", "Hoshangabad (Narmadapuram)", "Narmadapuram Hoshangabad"),
        ("Maharashtra", "Aurangabad", "Aurangabad"): ("Maharashtra", "Chhatrapati Sambhajinagar (Aurangabad)", "Chhatrapati Sambhajinagar"),
        ("Maharashtra", "Aurangabad", "Paithan"): ("Maharashtra", "Chhatrapati Sambhajinagar (Aurangabad)", "Paithan"),
        ("Maharashtra", "Aurangabad", "Vaijapur"): ("Maharashtra", "Chhatrapati Sambhajinagar (Aurangabad)", "Vaijapur"),
        ("Maharashtra", "Aurangabad", "Gangapur"): ("Maharashtra", "Chhatrapati Sambhajinagar (Aurangabad)", "Gangapur MH"),
        ("Maharashtra", "Aurangabad", "Kannad"): ("Maharashtra", "Chhatrapati Sambhajinagar (Aurangabad)", "Kannad"),
        ("Maharashtra", "Aurangabad", "Sillod"): ("Maharashtra", "Chhatrapati Sambhajinagar (Aurangabad)", "Sillod"),
        ("Maharashtra", "Osmanabad", "Osmanabad"): ("Maharashtra", "Dharashiv (Osmanabad)", "Dharashiv"),
        ("Maharashtra", "Osmanabad", "Tuljapur"): ("Maharashtra", "Dharashiv (Osmanabad)", "Tuljapur"),
        ("Maharashtra", "Osmanabad", "Omerga"): ("Maharashtra", "Dharashiv (Osmanabad)", "Omerga"),
        ("Maharashtra", "Osmanabad", "Paranda"): ("Maharashtra", "Dharashiv (Osmanabad)", "Paranda"),
        ("Maharashtra", "Ahmednagar", "Ahmednagar"): ("Maharashtra", "Ahmednagar (Ahilyanagar)", "Ahmednagar"),
        ("Maharashtra", "Ahmednagar", "Rahata"): ("Maharashtra", "Ahmednagar (Ahilyanagar)", "Rahata Shirdi"),
        ("Maharashtra", "Ahmednagar", "Sangamner"): ("Maharashtra", "Ahmednagar (Ahilyanagar)", "Sangamner"),
        ("Maharashtra", "Ahmednagar", "Kopargaon"): ("Maharashtra", "Ahmednagar (Ahilyanagar)", "Kopargaon"),
        ("Maharashtra", "Ahmednagar", "Shrirampur"): ("Maharashtra", "Ahmednagar (Ahilyanagar)", "Shrirampur"),
        ("Maharashtra", "Ahmednagar", "Newasa"): ("Maharashtra", "Ahmednagar (Ahilyanagar)", "Newasa"),
        ("Maharashtra", "Ahmednagar", "Parner"): ("Maharashtra", "Ahmednagar (Ahilyanagar)", "Parner"),
        ("Odisha", "Keonjhar", "Keonjhar"): ("Odisha", "Kendujhar (Keonjhar)", "Kendujhar Sadar"),
        ("Odisha", "Keonjhar", "Barbil"): ("Odisha", "Kendujhar (Keonjhar)", "Barbil"),
        ("Odisha", "Keonjhar", "Joda"): ("Odisha", "Kendujhar (Keonjhar)", "Joda"),
        ("Odisha", "Keonjhar", "Anandapur"): ("Odisha", "Kendujhar (Keonjhar)", "Anandapur"),
        ("Odisha", "Sonepur", "Sonepur"): ("Odisha", "Subarnapur (Sonepur)", "Sonepur Sadar"),
        ("Odisha", "Sonepur", "Birmaharajpur"): ("Odisha", "Subarnapur (Sonepur)", "Birmaharajpur"),
        ("Punjab", "Mohali", "Mohali"): ("Punjab", "Sahibzada Ajit Singh Nagar (Mohali)", "Mohali SAS Nagar"),
        ("Punjab", "Mohali", "Kharar"): ("Punjab", "Sahibzada Ajit Singh Nagar (Mohali)", "Kharar"),
        ("Punjab", "Mohali", "Dera Bassi"): ("Punjab", "Sahibzada Ajit Singh Nagar (Mohali)", "Dera Bassi"),
        ("Punjab", "Nawanshahr", "Nawanshahr"): ("Punjab", "Shahid Bhagat Singh Nagar (Nawanshahr)", "Nawanshahr"),
        ("Punjab", "Nawanshahr", "Balachaur"): ("Punjab", "Shahid Bhagat Singh Nagar (Nawanshahr)", "Balachaur"),
        ("Punjab", "Nawanshahr", "Banga"): ("Punjab", "Shahid Bhagat Singh Nagar (Nawanshahr)", "Banga"),
        ("Rajasthan", "Pratapgarh", "Pratapgarh"): ("Rajasthan", "Pratapgarh", "Pratapgarh Rajasthan"),
        ("Tamil Nadu", "Tuticorin", "Tuticorin"): ("Tamil Nadu", "Thoothukudi", "Thoothukudi Tuticorin"),
        ("Tamil Nadu", "Tuticorin", "Kovilpatti"): ("Tamil Nadu", "Thoothukudi", "Kovilpatti"),
        ("Tamil Nadu", "Tuticorin", "Tiruchendur"): ("Tamil Nadu", "Thoothukudi", "Tiruchendur"),
        ("Uttar Pradesh", "Lakhimpur Kheri", "Lakhimpur"): ("Uttar Pradesh", "Kheri (Lakhimpur)", "Lakhimpur"),
        ("Uttar Pradesh", "Lakhimpur Kheri", "Gola Gokaran Nath"): ("Uttar Pradesh", "Kheri (Lakhimpur)", "Gola Gokaran Nath"),
        ("Uttar Pradesh", "Lakhimpur Kheri", "Mohammadi"): ("Uttar Pradesh", "Kheri (Lakhimpur)", "Mohammadi"),
        ("Uttar Pradesh", "Allahabad", "Allahabad"): ("Uttar Pradesh", "Prayagraj (Allahabad)", "Prayagraj Sadar"),
        ("Uttar Pradesh", "Allahabad", "Phulpur"): ("Uttar Pradesh", "Prayagraj (Allahabad)", "Phulpur Allahabad"),
        ("Uttar Pradesh", "Allahabad", "Soraon"): ("Uttar Pradesh", "Prayagraj (Allahabad)", "Soraon"),
        ("Uttar Pradesh", "Allahabad", "Karchhana"): ("Uttar Pradesh", "Prayagraj (Allahabad)", "Karchhana"),
        ("Uttarakhand", "Udham Singh Nagar", "Rudrapur"): ("Uttarakhand", "Udham Singh Nagar", "Rudrapur US Nagar"),
        ("West Bengal", "Paschim Medinipur", "Midnapore"): ("West Bengal", "Paschim Medinipur", "Midnapore Sadar"),
        ("West Bengal", "Purba Medinipur", "Tamluk"): ("West Bengal", "Purba Medinipur", "Tamluk Sadar"),
        ("West Bengal", "Purba Medinipur", "Haldia"): ("West Bengal", "Purba Medinipur", "Haldia"),
        ("West Bengal", "Purba Medinipur", "Contai"): ("West Bengal", "Purba Medinipur", "Contai Kanthi")
    }

    # Apply explicit mappings
    for (old_s, old_d, old_a), (new_s, new_d, new_a) in mappings.items():
        cur.execute("""
            UPDATE crime_data 
            SET state = ?, district = ?, area = ? 
            WHERE state = ? AND district = ? AND area = ?
        """, (new_s, new_d, new_a, old_s, old_d, old_a))

    conn.commit()

    # For any remaining unmatched locations, insert them into locations and geo_areas so no crime data is orphaned
    cur.execute("""
        SELECT DISTINCT cd.state, cd.district, cd.area 
        FROM crime_data cd
        WHERE NOT EXISTS (
            SELECT 1 FROM locations l 
            WHERE l.state = cd.state AND l.district = cd.district AND l.area = cd.area
        )
    """)
    unmatched_rows = cur.fetchall()
    print(f"Remaining unmatched crime location tuples: {len(unmatched_rows)}")

    for st, dt, ar in unmatched_rows:
        # Check if state exists in geo_states
        cur.execute("SELECT id, state_code, lgd_state_code FROM geo_states WHERE state_name = ?", (st,))
        st_row = cur.fetchone()
        if not st_row:
            print(f"State not found: {st}")
            continue
        state_id, state_code, lgd_st_code = st_row

        # Check if district exists in geo_districts
        cur.execute("SELECT id, lgd_district_code FROM geo_districts WHERE state_id = ? AND district_name = ?", (state_id, dt))
        dt_row = cur.fetchone()
        if not dt_row:
            cur.execute("INSERT INTO geo_districts (state_id, state_name, district_name, lgd_district_code) VALUES (?, ?, ?, 9999)",
                        (state_id, st, dt))
            district_id = cur.lastrowid
            lgd_dt_code = 9999
        else:
            district_id, lgd_dt_code = dt_row

        # Insert area into geo_areas & locations
        cur.execute("""
            INSERT OR IGNORE INTO geo_areas (district_id, state_id, state_name, district_name, area_name, lgd_sub_district_code, area_type)
            VALUES (?, ?, ?, ?, ?, 99999, 'Tehsil / Taluk / Sub-District')
        """, (district_id, state_id, st, dt, ar))

        cur.execute("""
            INSERT OR IGNORE INTO locations (state, district, area, state_code, lgd_state_code, lgd_district_code, lgd_sub_district_code, area_type)
            VALUES (?, ?, ?, ?, ?, ?, 99999, 'Tehsil / Taluk / Sub-District')
        """, (st, dt, ar, state_code, lgd_st_code, lgd_dt_code))

    conn.commit()

    # Final Check
    cur.execute("""
        SELECT COUNT(*) FROM crime_data cd
        WHERE NOT EXISTS (
            SELECT 1 FROM locations l 
            WHERE l.state = cd.state AND l.district = cd.district AND l.area = cd.area
        )
    """)
    final_unmatched = cur.fetchone()[0]
    print(f"[Final Alignment Verification] Mismatched crime records: {final_unmatched} (0 Expected)")

    conn.close()

if __name__ == "__main__":
    reconcile()
