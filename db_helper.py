import pymysql
from config import Config

class DBHelper:
    def get_connection(self):
        """获取原始数据库连接（用于手动控制事务）"""
        return pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def fetch_all(self, sql, args=None):
        """查询多条记录"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, args)
                return cursor.fetchall()
        finally:
            conn.close()

    def fetch_one(self, sql, args=None):
        """查询单条记录"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, args)
                return cursor.fetchone()
        finally:
            conn.close()

    def execute_update(self, sql, args=None):
        """执行增删改（自动提交事务）"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                rows = cursor.execute(sql, args)
                conn.commit()
                return rows
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()