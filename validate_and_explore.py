import sqlite3
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect("petro_trade.db")


def run_query(query, title):
    """Utility function to execute and display SQL query results cleanly."""
    print(f"\n==================== {title} ====================")
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    return df


# 1. Total records, date ranges, and distinct entities
health_query = """
SELECT 
    COUNT(*) AS total_records,
    MIN(trade_date) AS earliest_date,
    MAX(trade_date) AS latest_date,
    COUNT(DISTINCT commodity_name) AS total_commodities,
    COUNT(DISTINCT reporter_country) AS total_reporters,
    COUNT(DISTINCT partner_country) AS total_partners
FROM trade_records;
"""
run_query(health_query, "DATASET HEALTH OVERVIEW")

# 2. Check for missing or zero values in key numerical columns
null_check_query = """
SELECT 
    SUM(CASE WHEN trade_volume_mt = 0 OR trade_volume_mt IS NULL THEN 1 ELSE 0 END) AS zero_or_null_volumes,
    SUM(CASE WHEN trade_value_usd = 0 OR trade_value_usd IS NULL THEN 1 ELSE 0 END) AS zero_or_null_values,
    SUM(CASE WHEN unit_price_usd = 0 OR unit_price_usd IS NULL THEN 1 ELSE 0 END) AS zero_or_null_prices,
    SUM(CASE WHEN unit_price_usd LIKE '%inf%' THEN 1 ELSE 0 END) AS infinity_count
FROM trade_records;
"""
run_query(null_check_query, "NULL & ZERO VALUE CHECK")

# Unit price summary stats per commodity
price_stats_query = """
SELECT 
    commodity_name,
    COUNT(*) AS transaction_count,
    ROUND(MIN(unit_price_usd), 2) AS min_price_usd_mt,
    ROUND(AVG(unit_price_usd), 2) AS avg_price_usd_mt,
    ROUND(MAX(unit_price_usd), 2) AS max_price_usd_mt
FROM trade_records
WHERE unit_price_usd > 0
GROUP BY commodity_name;
"""
run_query(price_stats_query, "UNIT PRICE SUMMARY STATS ($/MT)")

fob_cif_query = """
SELECT 
    commodity_name,
    ROUND(AVG(fobvalue / trade_volume_mt), 2) AS avg_fob_price_mt,
    ROUND(AVG(cifvalue / trade_volume_mt), 2) AS avg_cif_price_mt,
    ROUND(AVG((cifvalue - fobvalue) / trade_volume_mt), 2) AS estimated_freight_insurance_mt
FROM trade_records
WHERE fobvalue > 0 AND cifvalue > 0 AND trade_volume_mt > 0
GROUP BY commodity_name;
"""
run_query(fob_cif_query, "FOB VS CIF FREIGHT & INSURANCE MARGIN ANALYSIS")

# Top Exporters
exporters_query = """
SELECT 
    reporter_country AS exporting_nation,
    commodity_name,
    ROUND(SUM(trade_volume_mt), 2) AS total_volume_mt,
    ROUND(SUM(trade_value_usd) / 1000000.0, 2) AS total_value_million_usd
FROM trade_records
WHERE trade_type LIKE '%Export%' OR flowCode = 'X'
GROUP BY reporter_country, commodity_name
ORDER BY total_volume_mt DESC
LIMIT 5;
"""
run_query(exporters_query, "TOP 5 EXPORTING NATIONS BY VOLUME")

# Top Importers
importers_query = """
SELECT 
    reporter_country AS importing_nation,
    commodity_name,
    ROUND(SUM(trade_volume_mt), 2) AS total_volume_mt,
    ROUND(SUM(trade_value_usd) / 1000000.0, 2) AS total_value_million_usd
FROM trade_records
WHERE trade_type LIKE '%Import%' OR flowCode = 'M'
GROUP BY reporter_country, commodity_name
ORDER BY total_volume_mt DESC
LIMIT 5;
"""
run_query(importers_query, "TOP 5 IMPORTING NATIONS BY VOLUME")

conn.close()
print("\nValidation & EDA Complete!") 