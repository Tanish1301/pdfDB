import mysql.connector

# Connect to the MySQL server
conn = mysql.connector.connect(host="localhost", user="root", password="password")
cursor = conn.cursor()

# Create a new database
cursor.execute("CREATE DATABASE mydatabase")
conn.commit()

# Close the connection
conn.close()
