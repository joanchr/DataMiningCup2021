# -*- coding: utf-8 -*-
"""PCA_Items.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1BjFDmUk-LNuxB4omSGb6bGtMG5aDMCni

# Import
"""

from pyspark.sql import SparkSession

spark_session = SparkSession.builder.getOrCreate()

from pyspark.sql.functions import *

"""# Read Data"""

items = spark_session.read.option("inferSchema","true").csv("items.csv", header=True, sep="|")

# items.show(3)

"""# Data Preprocessing"""

# items.schema

items = items.withColumn("subtopics",translate(items["subtopics"],"[",""))
items = items.withColumn("subtopics",translate(items["subtopics"],"]",""))

"""### Delete Item 62676"""

# items.select([count(when(isnull('main topic'), True))]).show()
# items.select([count(when(isnull('subtopics'), True))]).show()
# items.select([count(when(isnull('subtopics') & isnull('main topic'), True))]).show()
# items.select([count(when(items["subtopics"] == "", True))]).show()

# items.where((isnull('subtopics') & isnull('main topic'))).show()

# items.where("itemID = 62676").show()

items = items.filter(items.itemID != 62676)

# items.where((isnull('subtopics') & isnull('main topic'))).show()

# items.show(3)

"""### Combine Main Topic and Subtopics"""

items = items.withColumn(
    "topics", 
    when(isnull("main topic"), items["subtopics"]).
    when(items["subtopics"] == "", items["main topic"]).
    otherwise(concat(col("main topic"), lit(","), col("subtopics")))
)

# items.show(3)
# items.where(isnull('main topic')).show(5)
# items.where(items["subtopics"] == "").show(3)

items = items.select("itemID","title","author","publisher","topics")

# items.show(3)

items = items.withColumn(
    'topics', array_distinct(split(col("topics"),","))
)

# items.select("topics").show(5, False)
# items.show(3)

"""### Explode into separate rows"""

from pyspark.sql.functions import explode

items = items.withColumn("topics_splitted", explode(items.topics))

# items.show(5)

items = items.drop("topics")

# items.show(3)

"""### Pivot"""

from pyspark.sql.functions import sum

spark_session.conf.set("spark.sql.pivotMaxValues",25000)

pivot = items.groupBy("itemID").pivot("topics_splitted").count()

pivot = pivot.fillna(0)

# pivot.show()

"""### Dimensionality Reduction"""

from pyspark.mllib.linalg import Vectors
from pyspark.mllib.linalg.distributed import RowMatrix

mat = pivot.drop("itemID").rdd.map(lambda s : Vectors.dense(s))

mat = RowMatrix(mat)

"""### Principal component analysis (PCA)"""

pca = mat.computePrincipalComponents(5)

projected = mat.multiply(pca)

# print(projected.rows.collect())