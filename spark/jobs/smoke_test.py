from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("smoke-test-s3a").getOrCreate()

df = spark.range(5).toDF("n")
df.write.mode("overwrite").parquet("s3a://tech-trends-silver/smoke_test/")

result = spark.read.parquet("s3a://tech-trends-silver/smoke_test/")
result.show()

print(f"SMOKE TEST OK: {result.count()} rows written and read back via s3a://")
