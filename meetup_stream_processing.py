# @Vipin Chaudhari

import sys, os
from pyspark.sql.functions import array, isnan, when, count, col, desc, from_json, array,lit
from pyspark.sql.types import StructType, StructField, StringType, ArrayType
from pyspark.sql import SparkSession, SQLContext
from pyspark import SparkConf
import constants as const


# Create a spark session
spark = SparkSession.builder.master("local[2]").appName("Stream Processing").getOrCreate()
spark.sparkContext._conf.getAll()

# I just want to have 2 tasks run in parallel since I am working on small dataset and single machine
spark.sparkContext._conf.setAll([('spark.sql.shuffle.partitions', '2'),('spark.executor.memory', '4g'), ('spark.app.name', 'Streaming App'), ('spark.executor.cores', '2'), ('spark.cores.max', '2'), ('spark.driver.memory','4g')])

spark.sparkContext.setLogLevel("ERROR")

# Read the Kafka stream into dataframe with the topic meetup-rsvp-topic
meetup_rsvp_df = spark.readStream.format("kafka"). \
    option("kafka.bootstrap.servers", const.kafka_server). \
    option("startingOffsets", "latest"). \
    option("subscribe", const.kafka_topic). \
    load()

# Inspect the stream schema
meetup_rsvp_df.printSchema()

# Get the value from kafka stream which is entire json documment
meetup_rsvp_1_df = meetup_rsvp_df.selectExpr("CAST(value AS STRING)", "CAST(timestamp AS TIMESTAMP)")

# Define the schema for structred streaming that matches json output from http://stream.meetup.com/2/rsvps.
meetup_rsvp_schema = StructType([
                        StructField("venue",
                            StructType([
                                StructField("venue_name", StringType(), True),
                                StructField("lon", StringType(), True),
                                StructField("lat", StringType(), True),
                                StructField("venue_id", StringType(), True)
                            ])
                        , True),
                        StructField("visibility", StringType(), True),
                        StructField("response", StringType(), True),
                        StructField("guests", StringType(), True),
                        StructField("member", 
                            StructType([
                                StructField("member_id", StringType(), True),
                                StructField("photo", StringType(), True),
                                StructField("member_name", StringType(), True)
                            ])
                        ),
                        StructField("rsvp_id", StringType(), True),
                        StructField("mtime", StringType(), True),
                        StructField("event", 
                            StructType([
                                StructField("event_name", StringType(), True),
                                StructField("event_id", StringType(), True),
                                StructField("time", StringType(), True),
                                StructField("event_url", StringType(), True)
                            ])
                        ),
                        StructField("group",
                            StructType([
                                StructField("group_topics",
                                    ArrayType(
                                        StructType([
                                            StructField("urlkey", StringType(), True),
                                            StructField("topic_name", StringType(), True)
                                        ])
                                    , True)
                                ),
                                StructField("group_city", StringType(), True),
                                StructField("group_country", StringType(), True),
                                StructField("group_id", StringType(), True),
                                StructField("group_name", StringType(), True),
                                StructField("group_lon", StringType(), True),
                                StructField("group_urlname", StringType(), True),
                                StructField("group_state", StringType(), True),
                                StructField("group_lat", StringType(), True)
                            ])
                        )
                    ])

# Convert the json stream into structred schema dataframe with schema defined above
meetup_rsvp_2_df = meetup_rsvp_1_df.select(from_json(col("value"), meetup_rsvp_schema).alias("message"), col("timestamp"))

# Normalize message.*
meetup_rsvp_3_df = meetup_rsvp_2_df.select("message.*", "timestamp")

# Normalize inner complex strctures like group.* into columns 
meetup_rsvp_4_df = meetup_rsvp_3_df.select(
    col("group.group_name").alias("GroupName"),
    col("group.group_country").alias("GroupCountry"),
    col("group.group_state").alias("GroupState"), 
    col("group.group_city").alias("GroupCity"),
    col("group.group_lat").alias("GroupLatitude"),
    col("group.group_lon").alias("GroupLongitude"),
    col("group.group_id").alias("GroupId"),
    col("group.group_topics").alias("GroupTopics"),
    col("member.member_id").alias("MemberId"),
    col("member.member_name").alias("MemberName"),
    col("response").alias("RSVPResponse"),
    col("guests").alias("Guests"),
    col("member.photo").alias("MemberPhoto"), 
    col("venue.venue_name").alias("VenueName"),
    col("venue.lon").alias("VenueLongitude"),
    col("venue.lat").alias("VenueLatitude"),
    col("venue.venue_id").alias("VenueId"),
    col("visibility").alias("Visibility"),
    col("event.event_name").alias("EventName"),
    col("event.event_id").alias("EventId"),
    col("event.time").alias("EventTime"),
    col("event.event_url").alias("EventURL")
)

mongodb_conn = "mongodb://" + const.mongodb_user + ":" + const.mongodb_pwd + "@" + const.mongodb_host + \
    ":27017/?authSource=admin"

# Write the stream records to mongodb
def write_to_mongodb(df, epoch_id):
    # epoc_id or batch_id is assigned auto by stream. We are capturing it to know different batches  
    df = df.withColumn("EpochId", lit(epoch_id))
    df.write.format("mongo").mode("append").options(uri=mongodb_conn, \
    database=const.mongodb_db, collection=const.mongodb_collection).save()

mongodb_stream = meetup_rsvp_4_df.writeStream.outputMode("update").foreachBatch(write_to_mongodb).start()
# mongodb_stream.awaitTermination()

meetup_rsvp_5_df = meetup_rsvp_4_df.groupBy("GroupName", "GroupCountry", \
      "GroupState", "GroupCity", "GroupLatitude", "GroupLongitude", "RSVPResponse") \
      .agg(count(col("RSVPResponse")).alias("ResponseCount"))

mysql_properties = {
    "driver": const.mysql_driver,
    "user": const.mysql_user,
    "password": const.mysql_pwd
}

# Aggregate the data and store it into MySQL
def write_to_mysql(df, epoch_id):
    df = df.withColumn("EpochId", lit(epoch_id))
    df = df.selectExpr("GroupName as GroupName", "GroupCountry", "GroupState", \
            "GroupCity", "GroupLatitude", "GroupLongitude", \
            "RSVPResponse", "ResponseCount", "EpochId")
    df.show()
    try:
        properties = {
            "driver": const.mysql_driver,
            "user": const.mysql_user,
            "password": const.mysql_pwd,
            "elideSetAutoCommits": "true"
        }
        df.write.jdbc(const.mysql_jdbc_url, const.mysql_tbl, "append", properties)
    except Exception as e:
        print(e)

# Display on console
# mysql_stream = meetup_rsvp_5_df.writeStream.outputMode("update").option("truncate", "false").format("console").start()

# Write to MongoDB collection
mysql_stream = meetup_rsvp_5_df.writeStream.outputMode("update").foreachBatch(write_to_mysql).start()

mysql_stream.awaitTermination()