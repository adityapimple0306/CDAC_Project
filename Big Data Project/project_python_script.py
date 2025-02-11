from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, regexp_replace, to_timestamp, trim, when, year, month, dayofweek, hour, min, max, count, sum
from pyspark.sql.window import Window
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType

# Initialize Spark session
spark = SparkSession.builder \
    .appName("ECommerceDataProcessing") \
    .config("spark.sql.shuffle.partitions", "4") \
    .config("spark.driver.memory", "8g") \
    .getOrCreate()

# Define batch size
BATCH_SIZE = 200000  

# HDFS Path
hdfs_path = "hdfs://localhost:9000/user/tejas/ecommerce_data/*.csv"

# Define the schema
schema = StructType([
    StructField("event_time", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("product_id", IntegerType(), True),
    StructField("category_id", StringType(), True),  # Ensure this is StringType
    StructField("category_code", StringType(), True),
    StructField("brand", StringType(), True),
    StructField("price", FloatType(), True),
    StructField("user_id", IntegerType(), True),
    StructField("user_session", StringType(), True)
])

# Read Data
df = spark.read.option("encoding", "UTF-8").csv(hdfs_path, header=True, schema=schema)

# Remove rows where price is negative or zero (assuming these are invalid)
df = df.filter(col("price") >= 0)

# Clean event_time
df = df.withColumn("event_time", lower(col("event_time")))
df = df.withColumn("event_time", trim(regexp_replace(col("event_time"), " utc", "")))
df = df.withColumn("event_time", to_timestamp(col("event_time"), "yyyy-MM-dd HH:mm:ss"))

# Fill Missing Values
df = df.fillna({"category_id": "-1", "category_code": "unknown", "brand": "unknown"}) 

# Convert event_type to numerical encoding
df = df.withColumn("event_type_numeric",
                   when(col("event_type") == "view", 1)
                   .when(col("event_type") == "cart", 2)
                   .when(col("event_type") == "remove_from_cart", 3)
                   .when(col("event_type") == "purchase", 4)
                   .otherwise(0))

# Add time-based features (year, month, day_of_week, hour)
df = df.withColumn("year", year(col("event_time"))) \
       .withColumn("month", month(col("event_time"))) \
       .withColumn("day_of_week", dayofweek(col("event_time"))) \
       .withColumn("hour", hour(col("event_time")))

# Session-based features
window_spec = Window.partitionBy("user_session")
df = df.withColumn("session_start", min("event_time").over(window_spec))
df = df.withColumn("session_end", max("event_time").over(window_spec))
df = df.withColumn("session_duration", (col("session_end").cast("long") - col("session_start").cast("long")))
df = df.withColumn("session_event_count", count("*").over(window_spec))

# User engagement metrics
df = df.withColumn("viewed", when(col("event_type") == "view", 1).otherwise(0)) \
       .withColumn("added_to_cart", when(col("event_type") == "cart", 1).otherwise(0)) \
       .withColumn("purchased", when(col("event_type") == "purchase", 1).otherwise(0))

user_engagement = df.groupBy("user_id") \
    .agg(sum("viewed").alias("total_views"),
         sum("added_to_cart").alias("total_add_to_cart"),
         sum("purchased").alias("total_purchases"))

user_engagement = user_engagement.withColumn("view_to_cart_rate", col("total_add_to_cart") / col("total_views")) \
                                 .withColumn("cart_to_purchase_rate", col("total_purchases") / col("total_add_to_cart"))

# Revenue analysis for Average Order Value (AOV)
session_revenue = df.filter(col("event_type") == "purchase") \
    .groupBy("user_session") \
    .agg(sum("price").alias("total_revenue"))

# MySQL Connection Details
mysql_url = "jdbc:mysql://localhost:3306/ecommerce_db"
mysql_properties = {
    "user": "root",
    "password": "manager",
    "driver": "com.mysql.cj.jdbc.Driver"
}

# Fix Column Type for category_id
df = df.withColumn("category_id", col("category_id").cast(StringType()))  # Ensure correct type for category_id

# Debug: Check schema before writing to MySQL
print("Schema before writing to MySQL:")
df.printSchema()

# Write Data to MySQL in Batches
df.write \
    .mode("append") \
    .option("batchsize", BATCH_SIZE) \
    .jdbc(mysql_url, "ecommerce_events", properties=mysql_properties)

# Write User Engagement Data to MySQL
user_engagement.write \
    .mode("append") \
    .option("batchsize", BATCH_SIZE) \
    .jdbc(mysql_url, "user_engagement", properties=mysql_properties)

# Write Session Revenue Data to MySQL
session_revenue.write \
    .mode("append") \
    .option("batchsize", BATCH_SIZE) \
    .jdbc(mysql_url, "session_revenue", properties=mysql_properties)

print("Data successfully written to MySQL in optimized mini-batches!")

# Stop Spark session
spark.stop()
