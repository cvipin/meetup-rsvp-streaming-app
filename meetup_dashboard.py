# @Vipin Chaudhari

import pandas as pd
import mysql.connector
import constants as const
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import MySQLdb
import pandas.io.sql as psql

meetup_db_conn = mysql.connector.connect(
  host=const.host,
  port="3306",
  user=const.mysql_user,
  password=const.mysql_pwd,
  database=const.mysql_db
)


sql_query = "SELECT LEFT(GroupName, 30) xLabel, GroupName, RSVPResponse, SUM(ResponseCount) ResponseCount \
            FROM meetup.MeetupRSVP \
            GROUP BY GroupName, RSVPResponse;"

from matplotlib.animation import FuncAnimation
import seaborn as sns

fig, ax1 = plt.subplots(figsize=(12, 6))

# Update the barplot realtime

def real_time_plot(i):
  # meetup_df = pd.read_sql(sql_query, db_connection)
  db_connection = MySQLdb.connect (host=const.host, port=3306,user=const.mysql_user,passwd=const.mysql_pwd,db=const.mysql_db)
  meetup_df = psql.read_sql(sql_query, con=db_connection)
  if meetup_df['GroupName'].count() > 0:
    meetup_df['TotalResponseCountByGroup'] = meetup_df.groupby(['GroupName'])['ResponseCount'].transform('sum')
    meetup_df = meetup_df.sort_values(by="TotalResponseCountByGroup", ascending=False)[:10]

    plt.cla()
    ax1=sns.barplot(data=meetup_df, x='GroupName', y='ResponseCount', hue='RSVPResponse')
    ylabels = ax1.get_yticks()
    ax1.set_yticklabels(ylabels, size=8)
    ax1.set_xticklabels(meetup_df['xLabel'], rotation=45, size=8)
    ax1.set_xlabel('Group Name')
    ax1.set_ylabel('# of Responses')
    plt.tight_layout()
  db_connection.close()

rt = FuncAnimation(plt.gcf(), real_time_plot, interval=1000)

plt.show()