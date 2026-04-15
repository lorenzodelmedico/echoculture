"""
Spark Wikipedia genre enrichment job.

Reads movies with genres=NULL from Postgres, distributes Wikipedia API calls
across Spark partitions (each respecting its own 1-1.5s rate limit), and
writes results back to Postgres.

Runs in local[4] mode from the Airflow container (Java 17 already present).
To run against a Spark cluster instead:
    .master("spark://spark-master:7077")
    and submit via: spark-submit --master spark://spark-master:7077 this_file.py
"""

import logging
import os
import random
import sys
import time

import psycopg2
from pyspark.sql import SparkSession

sys.path.insert(0, "/opt/airflow")
from scrapers.ecrantotal_pipeline import fetch_wikipedia_genres  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

PG_URL = os.environ["POSTGRES_URL"]
NUM_PARTITIONS = 4


def enrich_partition(rows):
    """
    Called once per Spark partition — runs inside a worker.
    Each partition opens its own Postgres connection and respects its own rate limit,
    so N partitions = N concurrent Wikipedia calls (all from the same IP, but at low
    aggregate rate — safe at our scale of ~200 movies/week).
    """
    conn = psycopg2.connect(PG_URL)
    cur = conn.cursor()
    updated = 0
    for row in rows:
        genres = fetch_wikipedia_genres(row["title"])
        if genres:
            cur.execute(
                "UPDATE movies SET genres = %s WHERE id = %s AND genres IS NULL",
                (genres, row["id"]),
            )
            updated += 1
        time.sleep(random.uniform(1.0, 1.5))
    conn.commit()
    cur.close()
    conn.close()
    return iter([{"updated": updated}])


def main():
    spark = (
        SparkSession.builder.appName("wikipedia-genre-enrichment")
        .master(f"local[{NUM_PARTITIONS}]")
        .config("spark.ui.port", "4040")
        .config("spark.driver.host", "localhost")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    conn = psycopg2.connect(PG_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM movies WHERE genres IS NULL ORDER BY id")
    rows = [{"id": r[0], "title": r[1]} for r in cur.fetchall()]
    cur.close()
    conn.close()

    if not rows:
        logging.info("No movies without genres — nothing to do.")
        spark.stop()
        return

    logging.info(
        f"{len(rows)} movies to enrich, split across {NUM_PARTITIONS} partitions."
    )
    rdd = spark.sparkContext.parallelize(rows, numSlices=NUM_PARTITIONS)
    results = rdd.mapPartitions(enrich_partition).collect()
    total = sum(r["updated"] for r in results)
    logging.info(f"✅ Spark enrichment complete. {total}/{len(rows)} movies updated.")
    spark.stop()


if __name__ == "__main__":
    main()
