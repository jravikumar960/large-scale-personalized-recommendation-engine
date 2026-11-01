from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("smoke").getOrCreate()
print("spark_version", spark.version)
spark.stop()
