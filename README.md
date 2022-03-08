# Data Warehouse with AWS
The repository shows how to create a data warehouse on AWS with S3 bucket and ETL pipeline for a database hosted on Redshift.


A music streaming startup, Sparkify, has grown their user base and song database and want to move their processes and data onto the cloud. Their data resides in S3, in a directory of JSON logs on user activity on the app, as well as a directory with JSON metadata on the songs in their app.

The role of this project is to build an ETL pipeline that extracts their data from S3, stages them in Redshift, and transforms data into a set of dimensional tables for their analytics team to continue finding insights into what songs their users are listening to. We'll be able to test the database and ETL pipeline by running queries given to us by the analytics team from Sparkify and compare our results with their expected results.

## Project Description
In this project, we'll apply the knowleadge on data warehouses and AWS to build an ETL pipeline for a database hosted on Redshift. We will need to load data from S3 to staging tables on Redshift and execute SQL statements that create the analytics tables from these staging tables.

## Project Structure
The project includes the following files and folders:

```bash
.
├── README.md
├── create_cluster.ipynb
├── create_tables.py
├── dwh.cfg
├── etl.py
├── images
│   ├── AWS_IAM_1.png
│   └── AWS_IAM_2.png
├── redshift_cluster.py
├── requirements.txt
└── sql_queries.py
```

- `README.md` - a markdown file giving an overview of the project and explaining the project structure.
- `redshift_cluster.py` - creates infrastructure (IAM role and cluster) as code
- `create_tables.py` - creates fact and dimension tables for the star schema in `Redshift`.
- `create_cluster.ipynb` - Jupyter notebook containing details of Infractructure as a code.
- `etl.py` - script connects to the Sparkify redshift database, loads `log_data` and `song_data` from `S3` into staging tables on `Redshift`, and transforms/process that data into the five analytics tables on `Redshift`.
- `sql_queries.py` - is where we define SQL statements, which will be imported into the two other files above.
- `dwh.cfg` - configuration file for `IAM`, `S3` bucket and `Redshift` cluster.


## Project Datasets
We'll be working with two datasets that reside in S3. Here are the S3 links for each:

- Song data: `s3://udacity-dend/song_data`
- Log data: `s3://udacity-dend/log_data`

Log data json path: s3://udacity-dend/log_json_path.json

### Song Dataset
The first dataset is a subset of real data from the [Million Song Dataset](http://millionsongdataset.com/). Each file is in JSON format and contains metadata about a song and the artist of that song. The files are partitioned by the first three letters of each song's track ID. For example, here are file paths to two files in this dataset.

```bash
song_data/A/B/C/TRABCEI128F424C983.json
song_data/A/A/B/TRAABJL12903CDCF1A.json
```

And below is an example of what a single song file, `TRAABJL12903CDCF1A.json`, looks like.

```bash
{"num_songs": 1, "artist_id": "ARJIE2Y1187B994AB7", "artist_latitude": null, "artist_longitude": null, "artist_location": "", "artist_name": "Line Renaud", "song_id": "SOUPIRU12A6D4FA1E1", "title": "Der Kleine Dompfaff", "duration": 152.92036, "year": 0}
```

### Log Dataset
The second dataset consists of log files in JSON format generated by this [event simulator](https://github.com/Interana/eventsim) based on the songs in the dataset above. These simulate app activity logs from an imaginary music streaming app based on configuration settings.

The log files in the dataset you'll be working with are partitioned by year and month. For example, here are file paths to two files in this dataset.

```bash
log_data/2018/11/2018-11-12-events.json
log_data/2018/11/2018-11-13-events.json
```

And below is an example of what the data in a log file, `2018-11-12-events.json`, looks like.

```
{"artist":null,"auth":"Logged In","firstName":"Kevin","gender":"M","itemInSession":0,"lastName":"Arellano","length":null,"level":"free","location":"Harrisburg-Carlisle, PA","method":"GET","page":"Home","registration":1540006905796.0,"sessionId":514,"song":null,"status":200,"ts":1542069417796,"userAgent":"\"Mozilla\/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit\/537.36 (KHTML, like Gecko) Chrome\/36.0.1985.125 Safari\/537.36\"","userId":"66"}
{"artist":"Fu","auth":"Logged In","firstName":"Kevin","gender":"M","itemInSession":1,"lastName":"Arellano","length":280.05832,"level":"free","location":"Harrisburg-Carlisle, PA","method":"PUT","page":"NextSong","registration":1540006905796.0,"sessionId":514,"song":"Ja I Ty","status":200,"ts":1542069637796,"userAgent":"\"Mozilla\/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit\/537.36 (KHTML, like Gecko) Chrome\/36.0.1985.125 Safari\/537.36\"","userId":"66"}
{"artist":null,"auth":"Logged In","firstName":"Maia","gender":"F","itemInSession":0,"lastName":"Burke","length":null,"level":"free","location":"Houston-The Woodlands-Sugar Land, TX","method":"GET","page":"Home","registration":1540676534796.0,"sessionId":510,"song":null,"status":200,"ts":1542071524796,"userAgent":"\"Mozilla\/5.0 (Windows NT 6.3; WOW64) AppleWebKit\/537.36 (KHTML, like Gecko) Chrome\/36.0.1985.143 Safari\/537.36\"","userId":"51"}
```

## Database Schema 
### Staging tables
We will first load `log_data` and `song_data` into two staging tables, which will be later on transforms them into the final five database tables. The staging tables are the following:

- `staging_songs` - Data about songs and the artists of those songs 
- `staging_logs` - activity logs of users

### Staging tables
Using the song and event datasets, we create a star schema optimized for queries on song play analysis. This includes the following tables.

**Fact Table**
- `songplays` - records in event data associated with song plays i.e. records with page NextSong 
  - *songplay_id, start_time, user_id, level, song_id, artist_id, session_id, location, user_agent*
 
**Dimension Tables**
- `users` - users in the app
  - *user_id, first_name, last_name, gender, level*

- `songs` - songs in music database
  - *song_id, title, artist_id, year, duration*
 
- `artists` - artists in music database
  - *artist_id, name, location, lattitude, longitude*

- `time` - timestamps of records in `songplays` broken down into specific units
  - *start_time, hour, day, week, month, year, weekday*

## Project Steps

Create the following environmental variables to enable access to AWS:

```bash
export AWS_ACCESS_KEY_ID=<replace with your access key id>
export AWS_SECRET_ACCESS_KEY=<replace with your secret access key>
```

An alternative way using a config file `dwh.cfg` containing all config parameters will be used in this project.

### Create and Configure DWH Infrastructure
- Create a new `IAM user` - IAM service is a global service, meaning newly created IAM users are not restricted to a specific region by default.
- Create clients for `IAM`, `EC2`, `S3` and `Redshift`
- Create `IAM Role` - Create an IAM Role that makes Redshift able to access S3 bucket (ReadOnly) which is done attaching the specified ReadOnly policy
- Create a `RedShift Cluster` - once created, save the cluster endpoint `DWH_ENDPOINT` and role `DWH_ROLE_ARN` in the config file
- Open an incoming `TCP` port to access the cluster ednpoint

### Create Table Schemas
- Design schemas for your fact and dimension tables
- Write a SQL `CREATE` statement for each of these tables in `sql_queries.py`
- Complete the logic in `create_tables.py` to connect to the database and create these tables
- Write SQL `DROP` statements to drop tables in the beginning of `create_tables.py` if the tables already exist. This way, you can run `create_tables.py` whenever you want to reset your database and test your ETL pipeline.
- Launch a redshift cluster and create an `IAM` role that has read access to `S3`.
- Add redshift database and `IAM` role info to `dwh.cfg`.
- Test by running `create_tables.py` and checking the table schemas in your redshift database. You can use Query Editor in the AWS Redshift console for this.

### ETL Pipeline
- Loading data from `S3` to staging tables on `Redshift`.
- Loading data from staging tables to analytics tables on `Redshift`

> Note: You can test by running `etl.py` after running `create_tables.py` and running the analytic queries on your Redshift database to compare your results with the expected results.

### Cleaning Resources
If we don't need the implemented DWH and would like to delete all relevant resources, type the following command:

```bash
python redshift_cluster.py delete
```

This will delete the IAM role as weel as the Redshift cluster.
