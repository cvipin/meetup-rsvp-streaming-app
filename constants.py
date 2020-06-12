# @Vipin Chaudhari


host='192.168.1.15'

meetup_rsvp_stream_api_url = "http://stream.meetup.com/2/rsvps"

# Kafka info
kafka_topic = "meetup-rsvp-topic"
kafka_server = host+':9092'

# MySQL info
mysql_user = "python"
mysql_pwd = "python"
mysql_db = "meetup"
mysql_driver = "com.mysql.cj.jdbc.Driver"
mysql_tbl = "MeetupRSVP"
mysql_jdbc_url = "jdbc:mysql://" + host + ":3306/" + mysql_db + "?useJDBCCompliantTimezoneShift=true&useLegacyDatetimeCode=false&serverTimezone=UTC"

# MongoDB info
mongodb_host=host
mongodb_user = "admin"
mongodb_pwd = "admin"
mongodb_db = "meetup"
mongodb_collection = "tbl_meetup_rsvp"