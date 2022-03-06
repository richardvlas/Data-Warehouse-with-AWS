# Data Warehouse with AWS
The repository shows how to create a data warehouse on AWS with S3 bucket and ETL pipeline for a database hosted on Redshift.


A music streaming startup, Sparkify, has grown their user base and song database and want to move their processes and data onto the cloud. Their data resides in S3, in a directory of JSON logs on user activity on the app, as well as a directory with JSON metadata on the songs in their app.

The role of this project is to build an ETL pipeline that extracts their data from S3, stages them in Redshift, and transforms data into a set of dimensional tables for their analytics team to continue finding insights into what songs their users are listening to. We'll be able to test the database and ETL pipeline by running queries given to us by the analytics team from Sparkify and compare our results with their expected results.

## Project Description
In this project, we'll apply the knowleadge on data warehouses and AWS to build an ETL pipeline for a database hosted on Redshift. We will need to load data from S3 to staging tables on Redshift and execute SQL statements that create the analytics tables from these staging tables.

## Project Structure
The project includes the following files and folders:

TODO: Add folder tree


- `README.md` - a markdown file giving an overview of the project and explaining the project structure.
- `create_table.py` - creates fact and dimension tables for the star schema in `Redshift`.
- `etl.py` - script connects to the Sparkify redshift database, loads `log_data` and `song_data` from `S3` into staging tables on `Redshift`, and transforms/process that data into the five analytics tables on `Redshift`.

- `sql_queries.py` is where we define SQL statements, which will be imported into the two other files above.


## Project Datasets



