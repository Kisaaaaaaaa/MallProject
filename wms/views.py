from flask import Blueprint, render_template, request, jsonify
from db_helper import DBHelper

wms_bp = Blueprint('wms', __name__)
db = DBHelper()


@wms_bp.route('/')
def dashboard():
    """
    WMS 库存控制台页面
    功能：展示所有仓库、SKU列表以及当前的物理库存分布
    """
    # 1. 获取所有仓库 (用于下拉框)
    warehouses = db.fetch_all("SELECT * FROM wms_ware_info")

    # 2. 获取所有可补货的 SKU (用于下拉框选择商品)
    # 关联查询 PMS 商品主表，为了获取商品名称
    sql_skus = """
        SELECT s.id, p.name as product_name, s.sp_data, s.sku_code 
        FROM pms_sku_stock s 
        JOIN pms_product p ON s.product_id = p.id
        ORDER BY p.id DESC
    """
    skus = db.fetch_all(sql_skus)

    # 3. 查询当前库存分布 (用于列表展示)
    # 四表关联：WMS库存 -> 仓库 -> SKU -> 商品
    sql_stock = """
        SELECT 
            ws.id,
            wi.name AS ware_name,
            p.name AS product_name,
            s.sku_code,
            s.sp_data,
            ws.stock,
            ws.stock_locked
        FROM wms_ware_sku ws
        JOIN wms_ware_info wi ON ws.ware_id = wi.id
        JOIN pms_sku_stock s ON ws.sku_id = s.id
        JOIN pms_product p ON s.product_id = p.id
        ORDER BY ws.id DESC
    """
    stocks = db.fetch_all(sql_stock)

    return render_template('wms_dashboard.html', warehouses=warehouses, skus=skus, stocks=stocks)


@wms_bp.route('/add_stock', methods=['POST'])
def add_stock():
    """
    入库/补货接口
    核心逻辑：事务控制，同时更新物理库存和销售库存
    """
    ware_id = request.form.get('ware_id')
    sku_id = request.form.get('sku_id')
    quantity = request.form.get('quantity')

    # 简单校验
    if not all([ware_id, sku_id, quantity]):
        return jsonify({'code': 400, 'msg': '参数不完整'})

    try:
        qty = int(quantity)
        if qty <= 0:
            return jsonify({'code': 400, 'msg': '补货数量必须大于0'})
    except ValueError:
        return jsonify({'code': 400, 'msg': '数量必须为整数'})

    conn = db.get_connection()
    try:
        conn.begin()  # 1. 开启事务 (Transaction Start)

        # 2. 检查 WMS 中是否已有该记录
        sql_check = "SELECT id FROM wms_ware_sku WHERE ware_id=%s AND sku_id=%s LIMIT 1"
        exists = None
        with conn.cursor() as cursor:
            cursor.execute(sql_check, (ware_id, sku_id))
            exists = cursor.fetchone()

        # 3. 更新或插入 WMS 物理库存表
        if exists:
            sql_wms_update = "UPDATE wms_ware_sku SET stock = stock + %s WHERE id=%s"
            with conn.cursor() as cursor:
                cursor.execute(sql_wms_update, (qty, exists['id']))
        else:
            sql_wms_insert = "INSERT INTO wms_ware_sku (ware_id, sku_id, stock, stock_locked) VALUES (%s, %s, %s, 0)"
            with conn.cursor() as cursor:
                cursor.execute(sql_wms_insert, (ware_id, sku_id, qty))

        # 4. 同步更新 PMS 销售库存表 (让前端用户能立刻买到)
        sql_pms_update = "UPDATE pms_sku_stock SET stock = stock + %s WHERE id=%s"
        with conn.cursor() as cursor:
            cursor.execute(sql_pms_update, (qty, sku_id))

        conn.commit()  # 5. 提交事务 (Commit)
        return jsonify({'code': 200, 'msg': f'成功入库 {qty} 件商品'})

    except Exception as e:
        conn.rollback()  # 6. 异常回滚 (Rollback)
        print(f"WMS Error: {e}")
        return jsonify({'code': 500, 'msg': '入库失败，请检查数据'})
    finally:
        conn.close()