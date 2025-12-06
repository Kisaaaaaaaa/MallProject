from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from db_helper import DBHelper

sys_bp = Blueprint('sys_admin', __name__)
db = DBHelper()


# =======================
# 1. 基础鉴权与控制台
# =======================

@sys_bp.before_request
def check_admin_login():
    """权限拦截器"""
    if request.endpoint == 'sys_admin.login':
        return
    if 'admin_id' not in session:
        return redirect(url_for('sys_admin.login'))


@sys_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        sql = "SELECT * FROM sys_admin WHERE username=%s AND password=%s"
        admin = db.fetch_one(sql, (username, password))

        if admin:
            # 检查账号状态 (之前报错 KeyError 的地方，现在已安全)
            if admin.get('status', 1) == 0:
                flash("该管理员账号已被禁用", "danger")
                return redirect(url_for('sys_admin.login'))

            # [关键修复] 登录管理员前，清除普通用户的脏数据！
            keys_to_remove = ['user_id', 'username', 'level_name', 'discount']
            for key in keys_to_remove:
                session.pop(key, None)

            # 设置管理员 Session
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['nick_name']
            return redirect(url_for('sys_admin.dashboard'))
        else:
            flash("管理员账号或密码错误", "danger")

    return render_template('admin_login.html')


@sys_bp.route('/logout')
def logout():
    """退出登录"""
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    # [优化] 退出后台后，跳转到商城首页，体验更流畅
    return redirect(url_for('pms.index'))


@sys_bp.route('/')
def dashboard():
    """后台数据看板"""
    res_sales = db.fetch_one("SELECT IFNULL(SUM(total_amount),0) as total FROM oms_order WHERE status > 0")
    res_orders = db.fetch_one("SELECT COUNT(*) as cnt FROM oms_order WHERE DATE(create_time) = CURDATE()")
    res_stock = db.fetch_one("SELECT COUNT(*) as cnt FROM pms_sku_stock WHERE stock < 10")
    latest_orders = db.fetch_all("SELECT * FROM oms_order ORDER BY create_time DESC LIMIT 5")

    return render_template('admin_dashboard.html',
                           sales=res_sales['total'],
                           today_orders=res_orders['cnt'],
                           low_stock=res_stock['cnt'],
                           orders=latest_orders)


# =======================
# 2. 商品管理 (多规格发布 & 智能创建)
# =======================

@sys_bp.route('/product/add', methods=['GET', 'POST'])
def product_add():
    if request.method == 'GET':
        cats = db.fetch_all("SELECT * FROM pms_category")
        brands = db.fetch_all("SELECT * FROM pms_brand")
        return render_template('admin_product_add.html', cats=cats, brands=brands)

    # POST 提交处理
    try:
        name = request.form.get('name')
        product_sn = request.form.get('product_sn')
        category_name = request.form.get('category_name').strip()
        brand_name = request.form.get('brand_name').strip()
        pic = request.form.get('pic')

        # 获取SKU数组
        sku_specs = request.form.getlist('sku_specs[]')
        sku_prices = request.form.getlist('sku_prices[]')
        sku_stocks = request.form.getlist('sku_stocks[]')

        if not category_name or not brand_name:
            flash("分类和品牌不能为空", "danger")
            return redirect(url_for('sys_admin.product_add'))

        # 计算展示价格 (最低价)
        price_list = [float(p) for p in sku_prices]
        min_price = min(price_list) if price_list else 0.00

        conn = db.get_connection()
        try:
            conn.begin()

            with conn.cursor() as cur:
                # A. 智能处理分类
                cur.execute("SELECT id FROM pms_category WHERE name=%s", (category_name,))
                cat_res = cur.fetchone()
                if cat_res:
                    cat_id = cat_res['id']
                else:
                    cur.execute("INSERT INTO pms_category (name, parent_id, level, sort) VALUES (%s, 0, 0, 0)",
                                (category_name,))
                    cat_id = cur.lastrowid

                # B. 智能处理品牌
                cur.execute("SELECT id FROM pms_brand WHERE name=%s", (brand_name,))
                brand_res = cur.fetchone()
                if brand_res:
                    brand_id = brand_res['id']
                else:
                    cur.execute("INSERT INTO pms_brand (name, product_count) VALUES (%s, 0)", (brand_name,))
                    brand_id = cur.lastrowid

                # C. 插入商品主表 (SPU)
                sql_prod = """
                    INSERT INTO pms_product 
                    (brand_id, category_id, name, pic, product_sn, publish_status, price, sale)
                    VALUES (%s, %s, %s, %s, %s, 1, %s, 0)
                """
                cur.execute(sql_prod, (brand_id, cat_id, name, pic, product_sn, min_price))
                new_pid = cur.lastrowid

                # D. 循环插入 SKU 库存表
                sql_sku = """
                    INSERT INTO pms_sku_stock (product_id, sku_code, price, stock, sp_data)
                    VALUES (%s, %s, %s, %s, %s)
                """

                for i in range(len(sku_specs)):
                    spec = sku_specs[i]
                    price = sku_prices[i]
                    stock = sku_stocks[i]
                    sku_code = f"{product_sn}_{i + 1}"

                    cur.execute(sql_sku, (new_pid, sku_code, price, stock, spec))

            conn.commit()
            flash(f"商品 '{name}' 发布成功！", "success")
            return redirect(url_for('sys_admin.dashboard'))

        except Exception as e:
            conn.rollback()
            print(e)
            flash(f"发布失败: {str(e)}", "danger")
            return redirect(url_for('sys_admin.product_add'))

    except Exception as e:
        flash("参数错误，请检查数值格式", "danger")
        return redirect(url_for('sys_admin.product_add'))


# =======================
# 3. 订单管理
# =======================

@sys_bp.route('/order/ship', methods=['POST'])
def order_ship():
    """订单发货接口"""
    order_id = request.form.get('order_id')
    db.execute_update("UPDATE oms_order SET status=2 WHERE id=%s", (order_id,))
    return jsonify({'code': 200, 'msg': '发货成功'})


# --- [新增] 商品列表管理 ---
@sys_bp.route('/product/list')
def product_list():
    """后台商品列表页"""
    # 只查询未逻辑删除的商品
    # 关联查询：为了显示库存，我们需要把 SKU 表里的库存加起来
    sql = """
        SELECT p.*, IFNULL(SUM(s.stock), 0) as total_stock 
        FROM pms_product p
        LEFT JOIN pms_sku_stock s ON p.id = s.product_id
        WHERE p.delete_status = 0 
        GROUP BY p.id 
        ORDER BY p.id DESC
    """
    products = db.fetch_all(sql)
    return render_template('admin_product_list.html', products=products)


@sys_bp.route('/product/delete', methods=['POST'])
def product_delete():
    """商品删除接口 (逻辑删除)"""
    pid = request.form.get('id')

    # 逻辑删除：设置 delete_status=1 且 publish_status=0 (下架)
    sql = "UPDATE pms_product SET delete_status = 1, publish_status = 0 WHERE id = %s"

    try:
        rows = db.execute_update(sql, (pid,))
        if rows > 0:
            return jsonify({'code': 200, 'msg': '删除成功'})
        else:
            return jsonify({'code': 400, 'msg': '删除失败或商品不存在'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})