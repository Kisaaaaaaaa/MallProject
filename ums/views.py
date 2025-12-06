from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from db_helper import DBHelper
import datetime

ums_bp = Blueprint('ums', __name__)
db = DBHelper()


# =======================
# 1. 登录与注册模块
# =======================

@ums_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("账号或密码不能为空", "danger")
            return redirect(url_for('ums.login'))

        # 关联查询：同时获取用户等级名称和折扣率
        sql = """
            SELECT u.*, l.name as level_name, l.discount 
            FROM ums_member u
            LEFT JOIN ums_member_level l ON u.member_level_id = l.id
            WHERE u.username=%s AND u.password=%s
        """
        user = db.fetch_one(sql, (username, password))

        if user:
            if user['status'] == 0:
                flash("账号已被禁用，请联系管理员", "danger")
                return redirect(url_for('ums.login'))

            # [关键修复] 登录普通用户前，彻底清除管理员状态！防止串号
            session.pop('admin_id', None)
            session.pop('admin_name', None)

            # 写入用户 Session
            session['user_id'] = user['id']
            session['username'] = user['nickname'] or user['username']
            session['level_name'] = user['level_name'] or '普通会员'
            session['discount'] = float(user['discount']) if user['discount'] else 1.0

            flash(f"欢迎回来，尊贵的 {session['level_name']}！", "success")
            return redirect(url_for('pms.index'))
        else:
            flash("账号或密码错误，请重试", "danger")

    return render_template('login.html')


@ums_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册 (包含自动创建地址)"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone')
        nickname = request.form.get('nickname') or username

        if not all([username, password, phone]):
            flash("请填写完整的注册信息", "warning")
            return redirect(url_for('ums.register'))

        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM ums_member WHERE username=%s", (username,))
                if cur.fetchone():
                    flash("该用户名已被注册", "warning")
                    return redirect(url_for('ums.register'))

                cur.execute("SELECT id FROM ums_member WHERE phone=%s", (phone,))
                if cur.fetchone():
                    flash("该手机号已被使用", "warning")
                    return redirect(url_for('ums.register'))

            conn.begin()

            # 1. 插入用户
            create_time = datetime.datetime.now()
            sql_user = """
                INSERT INTO ums_member 
                (member_level_id, username, password, nickname, phone, status, create_time)
                VALUES (1, %s, %s, %s, %s, 1, %s)
            """
            with conn.cursor() as cur:
                cur.execute(sql_user, (username, password, nickname, phone, create_time))
                new_user_id = cur.lastrowid

            # 2. 自动插入默认地址
            sql_addr = """
                INSERT INTO ums_member_receive_address 
                (member_id, name, phone_number, detail_address, default_status)
                VALUES (%s, %s, %s, '默认地址：学校/公司/家', 1)
            """
            with conn.cursor() as cur:
                cur.execute(sql_addr, (new_user_id, nickname, phone))

            conn.commit()

            flash("注册成功！已为您自动创建默认收货地址，请登录。", "success")
            return redirect(url_for('ums.login'))

        except Exception as e:
            conn.rollback()
            flash(f"注册失败: {str(e)}", "danger")
        finally:
            conn.close()

    return render_template('register.html')


@ums_bp.route('/logout')
def logout():
    """注销"""
    session.clear()
    return redirect(url_for('ums.login'))


# =======================
# 2. 地址管理模块
# =======================

@ums_bp.route('/address')
def address_list():
    if 'user_id' not in session: return redirect(url_for('ums.login'))
    sql = "SELECT * FROM ums_member_receive_address WHERE member_id=%s ORDER BY default_status DESC, id DESC"
    addresses = db.fetch_all(sql, (session['user_id'],))
    return render_template('user_address.html', addresses=addresses)


@ums_bp.route('/address/add', methods=['POST'])
def address_add():
    if 'user_id' not in session: return jsonify({'code': 401})
    name = request.form.get('name')
    phone = request.form.get('phone')
    detail = request.form.get('detail')
    user_id = session['user_id']

    conn = db.get_connection()
    try:
        conn.begin()
        with conn.cursor() as cur:
            cur.execute("UPDATE ums_member_receive_address SET default_status=0 WHERE member_id=%s", (user_id,))
        sql = "INSERT INTO ums_member_receive_address (member_id, name, phone_number, detail_address, default_status) VALUES (%s, %s, %s, %s, 1)"
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, name, phone, detail))
        conn.commit()
        return jsonify({'code': 200})
    except Exception as e:
        conn.rollback()
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        conn.close()


@ums_bp.route('/address/set_default', methods=['POST'])
def address_set_default():
    if 'user_id' not in session: return jsonify({'code': 401})
    addr_id = request.form.get('id')
    user_id = session['user_id']

    conn = db.get_connection()
    try:
        conn.begin()
        with conn.cursor() as cur:
            cur.execute("UPDATE ums_member_receive_address SET default_status=0 WHERE member_id=%s", (user_id,))
            cur.execute("UPDATE ums_member_receive_address SET default_status=1 WHERE id=%s AND member_id=%s",
                        (addr_id, user_id))
        conn.commit()
        return jsonify({'code': 200})
    except Exception as e:
        conn.rollback()
        return jsonify({'code': 500})
    finally:
        conn.close()


@ums_bp.route('/address/delete', methods=['POST'])
def address_delete():
    if 'user_id' not in session: return jsonify({'code': 401})
    addr_id = request.form.get('id')
    db.execute_update("DELETE FROM ums_member_receive_address WHERE id=%s AND member_id=%s",
                      (addr_id, session['user_id']))
    return jsonify({'code': 200})