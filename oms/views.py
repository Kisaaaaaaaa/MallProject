from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from db_helper import DBHelper
import uuid
import datetime

oms_bp = Blueprint('oms', __name__)
db = DBHelper()


# =======================
# 1. 购物车模块
# =======================

@oms_bp.route('/cart')
def view_cart():
    """查看购物车 (含会员折扣展示)"""
    if 'user_id' not in session:
        return redirect(url_for('ums.login'))

    user_id = session['user_id']

    # 获取会员折扣信息
    discount = session.get('discount', 1.0)
    level_name = session.get('level_name', '普通会员')

    # 1. 查询购物车
    sql_cart = "SELECT * FROM oms_cart_item WHERE member_id=%s ORDER BY create_date DESC"
    items = db.fetch_all(sql_cart, (user_id,))

    # 2. 计算金额
    # [修正] sum() 出来的结果是 Decimal 类型，需要转为 float 才能和 discount 相乘
    raw_total_decimal = sum([item['price'] * item['quantity'] for item in items])
    raw_total = float(raw_total_decimal)  # 转为浮点数

    discounted_total = raw_total * discount

    # 3. 查询可用优惠券
    now = datetime.datetime.now()
    sql_coupons = """
        SELECT h.id AS history_id, c.name, c.amount, c.min_point
        FROM sms_coupon_history h
        JOIN sms_coupon c ON h.coupon_id = c.id
        WHERE h.member_id = %s 
          AND h.use_status = 0 
          AND c.end_time > %s
          AND c.min_point <= %s
    """
    valid_coupons = []
    if discounted_total > 0:
        valid_coupons = db.fetch_all(sql_coupons, (user_id, now, discounted_total))

    return render_template('cart.html',
                           items=items,
                           total=discounted_total,
                           raw_total=raw_total,
                           discount=discount,
                           level_name=level_name,
                           coupons=valid_coupons)


@oms_bp.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session: return jsonify({'code': 401, 'msg': '请先登录'})
    sku_id = request.form.get('sku_id')
    quantity = int(request.form.get('quantity', 1))
    user_id = session['user_id']

    sku_sql = """
        SELECT s.id, s.price, s.sku_code, s.sp_data, p.id as pid, p.name, p.pic 
        FROM pms_sku_stock s
        JOIN pms_product p ON s.product_id = p.id
        WHERE s.id = %s
    """
    sku_info = db.fetch_one(sku_sql, (sku_id,))
    if not sku_info: return jsonify({'code': 404, 'msg': '规格不存在'})

    exist = db.fetch_one("SELECT id FROM oms_cart_item WHERE member_id=%s AND product_sku_id=%s", (user_id, sku_id))
    if exist:
        db.execute_update("UPDATE oms_cart_item SET quantity = quantity + %s WHERE id=%s", (quantity, exist['id']))
    else:
        insert = """
            INSERT INTO oms_cart_item (member_id, product_id, product_sku_id, quantity, price, product_pic, product_name, product_sku_code, product_attr)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        db.execute_update(insert, (
        user_id, sku_info['pid'], sku_info['id'], quantity, sku_info['price'], sku_info['pic'], sku_info['name'],
        sku_info['sku_code'], sku_info['sp_data']))

    return jsonify({'code': 200, 'msg': '已加入购物车'})


@oms_bp.route('/delete_cart_item', methods=['POST'])
def delete_cart_item():
    cart_id = request.form.get('cart_id')
    db.execute_update("DELETE FROM oms_cart_item WHERE id=%s", (cart_id,))
    return jsonify({'code': 200, 'msg': '已删除'})


# =======================
# 2. 订单交易模块
# =======================

@oms_bp.route('/submit_order', methods=['POST'])
def submit_order():
    """提交订单 (含会员折扣 + 优惠券)"""
    if 'user_id' not in session: return jsonify({'code': 401, 'msg': '登录已过期'})

    user_id = session['user_id']
    member_coupon_id = request.form.get('member_coupon_id')

    discount = session.get('discount', 1.0)

    cart_items = db.fetch_all("SELECT * FROM oms_cart_item WHERE member_id=%s", (user_id,))
    if not cart_items: return jsonify({'code': 400, 'msg': '购物车为空'})

    address = db.fetch_one(
        "SELECT * FROM ums_member_receive_address WHERE member_id=%s ORDER BY default_status DESC LIMIT 1", (user_id,))
    if not address: return jsonify({'code': 400, 'msg': '请先添加收货地址'})

    conn = db.get_connection()
    try:
        conn.begin()

        # A. 计算原始总价
        raw_decimal = sum([item['price'] * item['quantity'] for item in cart_items])
        raw_amount = float(raw_decimal)  # [修正] 转为 float

        # B. 应用会员折扣
        member_amount = raw_amount * discount
        final_amount = member_amount

        # C. 优惠券核销
        if member_coupon_id:
            sql_coupon = """
                SELECT h.id, c.amount, c.min_point, c.end_time 
                FROM sms_coupon_history h
                JOIN sms_coupon c ON h.coupon_id = c.id
                WHERE h.id = %s AND h.member_id = %s AND h.use_status = 0
            """
            with conn.cursor() as cur:
                cur.execute(sql_coupon, (member_coupon_id, user_id))
                coupon = cur.fetchone()

            if not coupon: raise Exception("优惠券无效")
            if coupon['end_time'] < datetime.datetime.now(): raise Exception("优惠券已过期")

            if member_amount < float(coupon['min_point']):  # [修正] min_point 也是 Decimal，需强转
                raise Exception(f"会员折后金额未满 {coupon['min_point']} 元，无法使用此券")

            # [修正] amount 也是 Decimal，需强转
            final_amount = max(0, member_amount - float(coupon['amount']))

            with conn.cursor() as cur:
                cur.execute("UPDATE sms_coupon_history SET use_status=1, use_time=NOW() WHERE id=%s",
                            (member_coupon_id,))

        # D. 生成订单
        order_sn = str(uuid.uuid1())
        sql_order = """
            INSERT INTO oms_order 
            (member_id, order_sn, total_amount, status, receiver_name, receiver_phone, receiver_detail_address)
            VALUES (%s, %s, %s, 0, %s, %s, %s)
        """
        with conn.cursor() as cur:
            cur.execute(sql_order, (
            user_id, order_sn, final_amount, address['name'], address['phone_number'], address['detail_address']))
            order_id = cur.lastrowid

            # E. 循环处理商品
        for item in cart_items:
            sql_stock = "UPDATE pms_sku_stock SET stock = stock - %s WHERE id = %s AND stock >= %s"
            with conn.cursor() as cur:
                affected = cur.execute(sql_stock, (item['quantity'], item['product_sku_id'], item['quantity']))
                if affected == 0: raise Exception(f"商品 {item['product_name']} 库存不足")

            sql_item = """
                INSERT INTO oms_order_item (order_id, order_sn, product_id, product_sku_id, product_name, product_price, product_quantity, product_attr)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            with conn.cursor() as cur:
                cur.execute(sql_item, (
                order_id, order_sn, item['product_id'], item['product_sku_id'], item['product_name'], item['price'],
                item['quantity'], item['product_attr']))

        # F. 清空购物车
        with conn.cursor() as cur:
            cur.execute("DELETE FROM oms_cart_item WHERE member_id=%s", (user_id,))

        conn.commit()
        return jsonify({'code': 200, 'msg': '下单成功', 'order_sn': order_sn})

    except Exception as e:
        conn.rollback()
        return jsonify({'code': 500, 'msg': f'下单失败: {str(e)}'})
    finally:
        conn.close()


# --- 订单列表接口 ---
@oms_bp.route('/my_orders')
def my_orders():
    if 'user_id' not in session: return redirect(url_for('ums.login'))
    orders = db.fetch_all("SELECT * FROM oms_order WHERE member_id=%s ORDER BY create_time DESC", (session['user_id'],))
    return render_template('order_list.html', orders=orders)


@oms_bp.route('/pay_order', methods=['POST'])
def pay_order():
    if 'user_id' not in session: return jsonify({'code': 401})
    order_id = request.form.get('order_id')
    user_id = session['user_id']
    order = db.fetch_one("SELECT id FROM oms_order WHERE id=%s AND member_id=%s AND status=0", (order_id, user_id))
    if not order: return jsonify({'code': 400, 'msg': '订单状态异常'})
    db.execute_update("UPDATE oms_order SET status=1 WHERE id=%s", (order_id,))
    return jsonify({'code': 200, 'msg': '支付成功！'})


@oms_bp.route('/cancel_order', methods=['POST'])
def cancel_order():
    if 'user_id' not in session: return jsonify({'code': 401})
    order_id = request.form.get('order_id')
    user_id = session['user_id']
    order = db.fetch_one("SELECT id FROM oms_order WHERE id=%s AND member_id=%s AND status=0", (order_id, user_id))
    if not order: return jsonify({'code': 400, 'msg': '无法取消'})
    db.execute_update("UPDATE oms_order SET status=4 WHERE id=%s", (order_id,))
    return jsonify({'code': 200, 'msg': '订单已取消'})


# --- [新增] 确认收货接口 ---
@oms_bp.route('/confirm_receipt', methods=['POST'])
def confirm_receipt():
    """
    用户确认收货
    逻辑：将订单状态从 2(已发货) 改为 3(已完成)
    """
    if 'user_id' not in session:
        return jsonify({'code': 401, 'msg': '请先登录'})

    order_id = request.form.get('order_id')
    user_id = session['user_id']

    # 1. 校验订单：必须属于当前用户，且状态必须是 2(已发货)
    # 防止用户恶意操作其他状态的订单
    order = db.fetch_one(
        "SELECT id FROM oms_order WHERE id=%s AND member_id=%s AND status=2",
        (order_id, user_id)
    )

    if not order:
        return jsonify({'code': 400, 'msg': '订单状态异常或不存在'})

    # 2. 更新状态为 3 (已完成)
    # 在真实业务中，这里可能还会触发增加积分、解冻分销佣金等逻辑
    try:
        db.execute_update("UPDATE oms_order SET status=3 WHERE id=%s", (order_id,))
        return jsonify({'code': 200, 'msg': '交易完成！'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})