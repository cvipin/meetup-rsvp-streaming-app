@Vipin Chaudhari

# Structured Streaming with Meetup RSVP stream.

Meetup provides access to rsvp stream with an [api endpoint](http://stream.meetup.com/2/rsvps). We will develop a streaming app with python, kafka, pyspark streaming, mongodb and mysql for fun.

- **Python:** Used for all required general coding
- **Kafka:** Kafka is used to stream meetup data to a kafka topic
- **Pyspark streaming:** Pyspark will subscribe to kafka topic and process the stream.
- **MongoDB:** Json messages processed by pyspark will be stored in MongoDB collection
- **MySQL:** Pyspark will aggregate the stream data and store in MySQL for real time reporting
- **Matplotlib:** A simple plot is created to demonstrate real time chart update

Architecture diagram:
![](/images/meetup_rsvp_architecture.png)

## Virtual Machine Setup
*Installation and setup of MongoDB, Python3, Jupyter, MySQL, Kafka*

----------

## Install CentOS7 on VirtualBox with GNOME desktop

I have installed CentOS 7 and setup the static ip of 192.168.1.15 with bridged connection. This helps me connect to guest os services from windows host. To avoid typing 192.168.1.15 in the applications you will be accessing, add an entry in hosts file to map name with ip

Host (Windows 10) will act as client and guest os (CentOS) will be server

----------

## MySQL installation and setup

Open the terminal and execute below commands:

    wget http://repo.mysql.com/mysql-community-release-el7-5.noarch.rpm
    sudo rpm -ivh mysql-community-release-el7-5.noarch.rpm
    sudo yum update
    sudo yum install mysql-server

Open MySQL port 3306

    sudo firewall-cmd --permanent --zone=trusted --add-port=3306/tcp
    sudo firewall-cmd  --reload

Start MySQL server

    sudo systemctl start mysqld

Connect to mysql

    mysql -u root -p

Create a user who can access MySQL from any host

    CREATE USER 'python'@'%' IDENTIFIED BY 'python';
    GRANT ALL PRIVILEGES ON *.* TO 'python'@'%' WITH GRANT OPTION;
    FLUSH PRIVILEGES;

Install [MySQL jdbc driver](https://dev.mysql.com/downloads/connector/j/5.1.html)

Mysql connection string:

	jdbc:mysql://192.168.1.15:3306?useJDBCCompliantTimezoneShift=true&useLegacyDatetimeCode=false&serverTimezone=UTC

Install Workbench/J to access MySQL from host if needed. Use the jdbc driver installed above. Driver class: com.mysql.cj.jdbc.Driver

----------

## MongoDB Installation and setup

1 Adding the MongoDB Repository
Create a repo for mongodb installation

    sudo vi /etc/yum.repos.d/mongodb-org-4.2.repo

Copy and paste below repository info to mongodb-org-4.2.repo

    [mongodb-org-4.2]
    name=MongoDB Repository
    baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/4.2/x86_64/
    gpgcheck=1
    enabled=1
    gpgkey=https://www.mongodb.org/static/pgp/server-4.2.asc

Verify that the repo is enabled:

    yum repolist

2 Installing MongoDB

    sudo yum install -y mongodb-org

Start mongoDB service

    sudo systemctl start mongod

Connect to mongo server to Create user

    mongo --port 27017

Create admin user

    use admin
    db.createUser(
      {
        user: "admin",
        pwd: "admin",
        roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
      }
    )

Edit mongo configuration

    sudo vi /etc/mongod.conf

Replace bindIp with below
 
    bindIp: 127.0.0.1,192.168.1.15


Open mongo server port 27017

    sudo firewall-cmd --permanent --zone=trusted --add-port=27017/tcp
    sudo firewall-cmd --permanent --zone=public --add-port=27017/tcp
    sudo firewall-cmd  --reload

Install MongoDB community compass to connect mongodb from host
https://www.mongodb.com/try/download/compass. Use below connection string format. If unable to connect make sure that mongod is running, port 27017 is open in guest. Use below Mongodb connection string:

    mongodb://admin:admin@192.168.1.15:27017/?authSource=admin

Check if port is open and mongod service is running

    sudo lsof -i
    sudo netstat -tulnp | grep mongod
    service mongod status


----------

# Kafka Installation and setup

1 Creating a User for Kafka

    sudo useradd kafka -m
    sudo passwd kafka
    sudo usermod -aG wheel kafka
    su -l kafka

2 Downloading and Extracting the Kafka Binaries

    mkdir ~/Downloads
    curl "https://downloads.apache.org/kafka/2.5.0/kafka_2.13-2.5.0.tgz" -o ~/Downloads/kafka.tgz
    mkdir ~/kafka && cd ~/kafka
    tar -xvzf ~/Downloads/kafka.tgz --strip 1

3 Configuring the Kafka Server. Create a file server.properties and add delete topic enable line at the end

    vi ~/kafka/config/server.properties
    delete.topic.enable = true

Also uncomment below and update with guest ip

	advertised.listeners=PLAINTEXT://192.168.1.15:9092
 
4 Creating Systemd Unit Files and Starting the Kafka Server

Create zookeeper.service:

    sudo vi /etc/systemd/system/zookeeper.service

Add below content to zookeeper.service:

    [Unit]
    Requires=network.target remote-fs.target
    After=network.target remote-fs.target
    
    [Service]
    Type=simple
    User=kafka
    ExecStart=/home/kafka/kafka/bin/zookeeper-server-start.sh /home/kafka/kafka/config/zookeeper.properties
    ExecStop=/home/kafka/kafka/bin/zookeeper-server-stop.sh
    Restart=on-abnormal
    
    [Install]
    WantedBy=multi-user.target

Create kafka.service:

    sudo vi /etc/systemd/system/kafka.service

Add below content to kafka.service:

    [Unit]
    Requires=zookeeper.service
    After=zookeeper.service
    
    [Service]
    Type=simple
    User=kafka
    ExecStart=/bin/sh -c '/home/kafka/kafka/bin/kafka-server-start.sh /home/kafka/kafka/config/server.properties > /home/kafka/kafka/kafka.log 2>&1'
    ExecStop=/home/kafka/kafka/bin/kafka-server-stop.sh
    Restart=on-abnormal
    
    [Install]
    WantedBy=multi-user.target

Start kafka and enable it

    sudo systemctl start kafka
    sudo systemctl status kafka
    sudo systemctl enable kafka

Open ports 9092 (kafka consumer/producer) and 2181 (zookeeper)

    sudo firewall-cmd --permanent --zone=public --add-port=9092/tcp
    sudo firewall-cmd --permanent --zone=public --add-port=2181/tcp
    sudo firewall-cmd  --reload

5 Test
Create a topic "TestTopic"

    ~/kafka/bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1 --topic TestTopic

Send test data to topic "TestTopic"

    echo "Streaming......now.." | ~/kafka/bin/kafka-console-producer.sh --broker-list localhost:9092 --topic TestTopic > /dev/null

Subscribe to "TestTopic" and see if above message is received

    ~/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic TestTopic --from-beginning

Download spark sql kafka jar and place it in spark installation jar directory

https://mvnrepository.com/artifact/org.apache.spark/spark-sql-kafka-0-10_2.11/2.4.5

copy spark-sql-kafka-0-10_2.11-2.4.5.jar to C:\Spark\jars

Note: Make sure to match the jar version with your scala and spark version. Inspect jars available in \jars directory to find out the pattern of existing jars

Download kafka clients and mongo connector jars
https://mvnrepository.com/artifact/org.apache.kafka/kafka-clients/2.4.0
https://mvnrepository.com/artifact/org.mongodb.spark/mongo-spark-connector_2.11/2.4.2
https://mvnrepository.com/artifact/org.mongodb/mongo-java-driver/3.12.5

kafka-clients-2.4.0.jar
mongo-spark-connector_2.11-2.4.2.jar
mongo-java-driver-3.12.5.jar

Place it in jars directory

----------

## Install Python 3

	sudo yum install -y python3
	alias python='/usr/bin/python3' # Use only for current session as yum is dependent on python2
	python --version

Install jupyter notebook

	sudo pip3 install jupyter

I like to access my jupyter notebook from host os. Below setup can be performed to allow host connecting to guest jupyter notebook

Open the default port 8888

	sudo firewall-cmd --zone=public --add-port=8888/tcp --permanent
	sudo firewall-cmd --reload

Generate jupyter config

	jupyter notebook --generate-config

Open the config

	vi ~/.jupyter/jupyter_notebook_config.py

Uncomment and update below properties:

	c.NotebookApp.open_browser = False
	c.NotebookApp.ip = '*'

Setup jupyter password (to avoid authentication token)

	jupyter notebook password


----------

## Install Apache Spark on host (Windows 10)

Install apache spark on host os and setup with below parameters. Install java 8 if not installed already. Setup environment variables as below:

	JAVA_HOME=C:\Program Files\Java\jdk1.8.0_241 # change as per your path
	SPARK_HOME=C:\Spark # change as per your path
	PATH=%SPARK_HOME%\bin;%JAVA_HOME%/bin # append
	PYTHONPATH=%SPARK_HOME%/python/lib/py4j-0.10.7-src.zip;%SPARK_HOME%/python # change the py4j version as per installed
	# set these if you want to open pyspark jupyter notebook by default
	PYSPARK_DRIVER_PYTHON="jupyter"
	PYSPARK_DRIVER_PYTHON_OPTS="notebook"

----------

## Install kafka libraries on host

	python -m pip install kafka-python

----------

## Install Apache Spark on guest (CentOS)

Make sure that Java 8 is installed

	wget http://archive.apache.org/dist/spark/spark-2.4.4/spark-2.4.4-bin-hadoop2.7.tgz
	sudo mkdir /usr/local/spark
	sudo tar -xzf spark-2.4.4-bin-hadoop2.7.tgz --strip-components 1 --directory /usr/local/spark

Edit bashrc

	sudo vi ~/.bashrc

Insert below export commands. This will make sure to open pyspark notebook

	export SPARK_HOME=/usr/local/spark
	export PATH=$PATH:$SPARK_HOME/bin
	export PYTHONPATH=$SPARK_HOME/python:$PYTHONPATH
	export PYSPARK_DRIVER_PYTHON="jupyter"
	export PYSPARK_DRIVER_PYTHON_OPTS="notebook"
	export PYSPARK_PYTHON=python
	export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.252.b09-2.el7_8.x86_64/jre
	export PATH=$PATH:$JAVA_HOME/bin

Refresh bashrc

	source ~/.bashrc

Run the pyspark command. This will start the jupyter notebook server

	pyspark

Open the notebook to see if it works and enter the password

	http://192.168.1.15:8888/


Start the services on guest if not already started

	Kafka service: sudo systemctl start kafka
	MySQL service: sudo systemctl start mysqld
	MongoDB service: sudo systemctl start mongod

## Run App

Open cmd and run the kafka producer app
	
	python kafka_producer.py

Open another cmd and run meetup stream processing app

	python meetup_stream_processing.py

To see realtime update to barplot open another cmd and run below python file

	python meetup_dashboard.py

Sample MongoDB output

![](/images/mongodb_collection.png)

Sample MySQL output

![](/images/mysql_table.png)

Sample Dashboard output

![](/images/realtime_plot.png)