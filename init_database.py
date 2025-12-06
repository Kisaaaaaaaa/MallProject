#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
自动执行 DB/init_db.sql 来初始化数据库
"""

import pymysql
from config import Config
import os
import getpass

def test_connection(password=None):
    """测试数据库连接"""
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=password or Config.DB_PASSWORD,
            charset='utf8mb4'
        )
        conn.close()
        return True, password or Config.DB_PASSWORD
    except pymysql.Error as e:
        return False, str(e)

def init_database():
    """初始化数据库"""
    # 首先测试数据库连接
    print("正在测试数据库连接...")
    success, result = test_connection()
    
    db_password = Config.DB_PASSWORD
    if not success:
        print(f"❌ 使用 config.py 中的密码连接失败: {result}")
        print("\n提示: 如果您的 MySQL root 密码不是 '123456'，请:")
        print("  1. 修改 config.py 中的 DB_PASSWORD")
        print("  2. 或者现在输入正确的密码")
        
        try:
            user_input = input("\n是否现在输入密码? (y/n，直接回车跳过): ").strip().lower()
            if user_input == 'y':
                db_password = getpass.getpass("请输入 MySQL root 密码: ")
                success, result = test_connection(db_password)
                if not success:
                    print(f"❌ 密码仍然不正确: {result}")
                    return False
                print("✅ 密码验证成功！")
            else:
                print("请先修改 config.py 中的 DB_PASSWORD，然后重新运行此脚本")
                return False
        except KeyboardInterrupt:
            print("\n\n已取消")
            return False
    
    try:
        # 连接到 MySQL 服务器（不指定数据库）
        print("正在连接 MySQL 服务器...")
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=db_password,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 读取 SQL 文件
        sql_file_path = os.path.join('DB', 'init_db.sql')
        print(f"正在读取 SQL 文件: {sql_file_path}")
        
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 使用简单的方法：按分号分割 SQL 语句
        # 先移除注释行
        lines = []
        for line in sql_content.split('\n'):
            stripped = line.strip()
            # 跳过空行和纯注释行
            if not stripped or stripped.startswith('--'):
                continue
            # 移除行内注释
            if '--' in line:
                line = line.split('--')[0].rstrip()
            if line.strip():
                lines.append(line)
        
        # 重新组合
        full_text = '\n'.join(lines)
        
        # 按分号分割语句（简单方法，假设 SQL 文件中没有字符串包含分号的情况）
        # 对于这个项目的 SQL 文件，这种方法应该足够
        statements = []
        for stmt in full_text.split(';'):
            stmt = stmt.strip()
            if stmt and not stmt.upper().startswith('--'):
                statements.append(stmt)
        
        # 执行所有 SQL 语句
        print(f"找到 {len(statements)} 条 SQL 语句，开始执行...")
        
        executed_count = 0
        for i, statement in enumerate(statements, 1):
            try:
                # 跳过空语句和纯注释
                stmt_clean = statement.strip()
                if not stmt_clean or stmt_clean.startswith('--') or stmt_clean == ';':
                    continue
                
                # 执行语句
                cursor.execute(statement)
                executed_count += 1
                
                # 每执行 10 条语句显示一次进度
                if executed_count % 10 == 0:
                    print(f"已执行 {executed_count} 条语句...")
                    
            except Exception as e:
                error_msg = str(e)
                # 如果是已存在的错误，可以忽略
                if any(keyword in error_msg for keyword in [
                    'Duplicate key name', 'already exists', 'Duplicate entry',
                    'Table', 'already exists', 'database exists'
                ]):
                    print(f"⚠️  语句 {i} 已存在（可能已初始化过），跳过")
                    continue
                else:
                    print(f"❌ 错误: 执行语句 {i} 时出错: {error_msg[:150]}")
                    # 显示语句的前100个字符以便调试
                    stmt_preview = statement.replace('\n', ' ').strip()[:100]
                    print(f"   语句预览: {stmt_preview}...")
                    # 继续执行其他语句
                    continue
        
        # 提交事务
        conn.commit()
        print(f"\n✅ 数据库初始化完成！共执行 {executed_count} 条语句")
        
        # 验证数据库和表是否创建成功
        cursor.execute("USE mall_b2c")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✅ 数据库 'mall_b2c' 已创建，包含 {len(tables)} 个表")
        
        cursor.close()
        conn.close()
        
        return True
        
    except pymysql.Error as e:
        print(f"❌ 数据库连接错误: {e}")
        print("\n请检查:")
        print("1. MySQL 服务是否正在运行")
        print(f"2. 数据库配置是否正确 (config.py)")
        print(f"   - 主机: {Config.DB_HOST}")
        print(f"   - 端口: {Config.DB_PORT}")
        print(f"   - 用户: {Config.DB_USER}")
        print(f"   - 密码: {'*' * len(Config.DB_PASSWORD)}")
        return False
    except FileNotFoundError:
        print(f"❌ 错误: 找不到 SQL 文件 {sql_file_path}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("数据库初始化工具")
    print("=" * 50)
    print()
    
    success = init_database()
    
    if success:
        print("\n" + "=" * 50)
        print("初始化成功！现在可以运行应用了:")
        print("  python app.py")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("初始化失败，请检查错误信息并重试")
        print("=" * 50)
        exit(1)

