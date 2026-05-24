import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="000",
        database="chihuahuadb",
        port=3307
    )