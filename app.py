import os
import time
import psycopg2

from flask import Flask, request, jsonify, Response
from psycopg2 import DatabaseError
from prometheus_client import start_http_server, Summary, Counter, generate_latest, CollectorRegistry, Histogram
app = Flask(__name__)

# przerywa po kilku sec., przerwanie kilkanaści ms, wyrzuca randomowo eroor 500 np
REQUEST_LATENCY_2MS = Summary('request_latency2ms_seconds', 'Latency of HTTP method in seconds')
REQUEST_LATENCY_2S = Summary('request_latency2s_seconds', 'Latency of HTTP method in seconds')
REQUEST_LATENCY_5S = Summary('request_latency5s_seconds', 'Latency of HTTP method in seconds')
# REQUEST_LATENCY = Summary('request_latency_seconds', 'Latency of HTTP method in seconds')
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Latency of HTTP requests in seconds', buckets=[0.5, 1, 2, 3, 5, 10])
ERROR_RATE = Counter("error_rate", "Total number of errors")
PASS_RATE = Counter("pass_rate", "Total number of successful requests")
REQUEST_COUNT = Counter('request_count', 'Total number of HTTP requests')

REGISTRY = CollectorRegistry()

REGISTRY.register(REQUEST_LATENCY_2MS)
REGISTRY.register(REQUEST_LATENCY)
REGISTRY.register(REQUEST_LATENCY_2S)
REGISTRY.register(REQUEST_LATENCY_5S)
REGISTRY.register(REQUEST_COUNT)
REGISTRY.register(PASS_RATE)
REGISTRY.register(ERROR_RATE)

@app.route("/metrics")
def metrics():
    return generate_latest(REGISTRY)


@app.route("/error", methods=["GET"])
def error():
    REQUEST_COUNT.inc()
    ERROR_RATE.inc()
    return jsonify({"message":"Database error occurred"}), 500

@app.route("/latency", methods=["GET"])
def latency():
    REQUEST_COUNT.inc()
    start = time.time()
    time.sleep(1)
    latency = time.time() - start
    REQUEST_LATENCY.observe(latency)
    return "Latency endpoint"


@app.route("/timeout", methods=["GET"])
def timeout():
    REQUEST_COUNT.inc()
    start = time.time()
    try:
        time.sleep(2)
    except Exception as e:
        ERROR_RATE.inc()
        return jsonify({"error": f"Error during timeout: {str(e)}"}), 500
    latency = time.time() - start
    REQUEST_LATENCY.observe(latency)
    PASS_RATE.inc()
    return jsonify({"message":"End after 2sec"}), 200

@app.route("/timeout5", methods=["GET"])
def timeout_5():
    REQUEST_COUNT.inc()
    start = time.time()
    try:
        time.sleep(5)
    except Exception as e:
        ERROR_RATE.inc()
        return jsonify({"error":f"Error during timeout: {str(e)}"}), 500

    latency = time.time() - start
    REQUEST_LATENCY.observe(latency)
    PASS_RATE.inc()
    return jsonify({"message":"End after 5sec"}), 200


@app.route("/mstimeout", methods=["GET"])
def ms_timeout():
    REQUEST_COUNT.inc()
    start = time.time()
    time.sleep(0.2)
    latency = time.time() - start
    REQUEST_LATENCY.observe(latency)
    PASS_RATE.inc()
    return jsonify({"message":"End after 20ms"}), 200



def db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "host.docker.internal"),
        database=os.getenv("DB_NAME", "microservices"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "bikeshop")
    )
    return conn


@app.route("/get", methods=["GET"])
def get():
    REQUEST_COUNT.inc()
    try:
        conn = db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM docker")
            data = cur.fetchall()
        PASS_RATE.inc()
        return jsonify(data), 200
    except (Exception, psycopg2.Error) as error:
        ERROR_RATE.inc()
        print("Error fetching data from database", error)
        return jsonify({"error":"Database error occurred"}), 500


@app.route("/add", methods=["POST"])
def add():
    REQUEST_COUNT.inc()
    x = request.get_json()
    try:
        conn = db_connection()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO docker (item_id, data) VALUES (%s, %s)", (x["item_id"], x["data"]))
        conn.commit()
        PASS_RATE.inc()
        return jsonify({"message":"Added"}), 201
    except (Exception, psycopg2.Error) as error:
        ERROR_RATE.inc()
        print("Error adding data to database", error)
        return jsonify({"error":"Database error occurred"}), 500


@app.route("/put/<int:id>", methods=["PUT"])
def modify(id):
    REQUEST_COUNT.inc()
    x = request.get_json()
    try:
        conn = db_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE docker SET data = %s WHERE id = %s", (x["data"], id))
        conn.commit()
        PASS_RATE.inc()
        return jsonify({"message":"Modified"}), 200
    except (Exception, psycopg2.Error) as error:
        ERROR_RATE.inc()
        print("Error modifying data in database", error)
        return jsonify({"error":"Database error occurred"}), 500

@app.route("/delete/<int:id>", methods=["DELETE"])
def delete(id):
    REQUEST_COUNT.inc()
    try:
        conn = db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM docker WHERE id = %s", (id,))
        conn.commit()
        PASS_RATE.inc()
        return jsonify({"message":"Deleted"}), 200
    except (Exception, psycopg2.Error) as error:
        ERROR_RATE.inc()
        print("Error deleting data from database", error)
        return jsonify({"error":"Database error occurred"}), 500



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)

