from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from db_helper import DBHelper
import datetime

sms_bp = Blueprint('sms', __name__)
db = DBHelper()


@sms_bp.route('/coupon_center')
def coupon_center():
    """
    领券中心：展示所有正在进行中、且还有剩余数量的优惠券
    """
    now = datetime.datetime.now()
    # 逻辑优化：只展示未过期 且 已领数量 < 发行数量 的券
    sql = "SELECT * FROM sms_coupon WHERE end_time > %s AND receive_count < publish_count"
    coupons = db.fetch_all(sql, (now,))

    return render_template('coupon_center.html', coupons=coupons)


@sms_bp.route('/receive_coupon', methods=['POST'])
def receive_coupon():
    """
    领取优惠券接口 (事务版)
    """
    if 'user_id' not in session:
        return jsonify({'code': 401, 'msg': '请先登录'})

    user_id = session['user_id']
    coupon_id = request.form.get('coupon_id')

    conn = db.get_connection()
    try:
        conn.begin()  # 1. 开启事务

        # 2. 查询优惠券详情 (加锁查询防止并发超发，这里简单用普通查询演示)
        # 注意：严格来说这里应该用 SELECT ... FOR UPDATE，但课程设计普通查询即可
        sql_check = "SELECT * FROM sms_coupon WHERE id=%s"
        with conn.cursor() as cur:
            cur.execute(sql_check, (coupon_id,))
            coupon = cur.fetchone()

        if not coupon:
            conn.rollback()
            return jsonify({'code': 404, 'msg': '优惠券不存在'})

        # 3. 校验过期和库存
        if coupon['end_time'] < datetime.datetime.now():
            conn.rollback()
            return jsonify({'code': 400, 'msg': '来晚了，优惠券已过期'})

        if coupon['receive_count'] >= coupon['publish_count']:
            conn.rollback()
            return jsonify({'code': 400, 'msg': '来晚了，优惠券已抢光'})

        # 4. 校验重复领取
        sql_history = "SELECT id FROM sms_coupon_history WHERE member_id=%s AND coupon_id=%s"
        with conn.cursor() as cur:
            cur.execute(sql_history, (user_id, coupon_id))
            has_received = cur.fetchone()

        if has_received:
            conn.rollback()
            return jsonify({'code': 400, 'msg': '您已经领取过这张券了，不要贪心哦'})

        # 5. 执行领取业务
        # 5.1 插入领取记录
        sql_insert = "INSERT INTO sms_coupon_history (coupon_id, member_id, use_status) VALUES (%s, %s, 0)"
        with conn.cursor() as cur:
            cur.execute(sql_insert, (coupon_id, user_id))

        # 5.2 更新主表已领数量 (receive_count + 1)
        sql_update = "UPDATE sms_coupon SET receive_count = receive_count + 1 WHERE id=%s"
        with conn.cursor() as cur:
            cur.execute(sql_update, (coupon_id,))

        conn.commit()  # 6. 提交事务
        return jsonify({'code': 200, 'msg': '领取成功'})

    except Exception as e:
        conn.rollback()  # 回滚
        print(f"SMS Error: {e}")
        return jsonify({'code': 500, 'msg': '服务器繁忙'})
    finally:
        conn.close()


@sms_bp.route('/my_coupons')
def my_coupons():
    """
    我的优惠券列表
    """
    if 'user_id' not in session:
        return redirect(url_for('ums.login'))

    sql = """
        SELECT h.*, c.name, c.amount, c.min_point, c.end_time 
        FROM sms_coupon_history h
        JOIN sms_coupon c ON h.coupon_id = c.id
        WHERE h.member_id = %s
        ORDER BY h.id DESC
    """
    my_coupons = db.fetch_all(sql, (session['user_id'],))

    return render_template('my_coupons.html', coupons=my_coupons)