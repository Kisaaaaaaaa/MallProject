from flask import Blueprint, render_template, request, redirect, url_for
from db_helper import DBHelper

pms_bp = Blueprint('pms', __name__)
db = DBHelper()


@pms_bp.route('/index')
@pms_bp.route('/')
def index():
    """
    商城首页 / 商品列表页
    """
    keyword = request.args.get('keyword', '')
    category_id = request.args.get('cid', '')

    # 1. 基础查询 SQL
    # [修正] 去掉了 p.sub_title，增加了 p.sale (销量)
    sql = """
        SELECT 
            p.id, 
            p.name, 
            p.pic, 
            p.product_sn, 
            p.sale, 
            IFNULL(MIN(s.price), p.price) as show_price,
            IFNULL(SUM(s.stock), 0) as total_stock
        FROM pms_product p
        LEFT JOIN pms_sku_stock s ON p.id = s.product_id
        WHERE p.publish_status = 1 AND p.delete_status = 0
    """

    params = []

    # 2. 动态拼接筛选条件
    if keyword:
        sql += " AND p.name LIKE %s"
        params.append(f'%{keyword}%')

    if category_id:
        sql += " AND p.category_id = %s"
        params.append(category_id)

    # 3. 分组与排序 (按 sort 排序，如果没有则按 ID 倒序)
    sql += " GROUP BY p.id ORDER BY p.id DESC"

    products = db.fetch_all(sql, params)

    # 4. 获取所有分类 (用于侧边栏导航)
    categories = db.fetch_all("SELECT * FROM pms_category WHERE parent_id = 0 ORDER BY sort DESC")

    return render_template('index.html',
                           products=products,
                           categories=categories,
                           curr_cid=category_id,
                           curr_kw=keyword)


@pms_bp.route('/detail/<int:product_id>')
def detail(product_id):
    """
    商品详情页
    """
    # 1. 获取商品主信息
    product = db.fetch_one("SELECT * FROM pms_product WHERE id=%s", (product_id,))
    if not product:
        return "商品不存在或已下架", 404

    # 2. 获取该商品下的所有 SKU (规格)
    skus = db.fetch_all("SELECT * FROM pms_sku_stock WHERE product_id=%s ORDER BY price ASC", (product_id,))

    # 3. 获取品牌信息
    brand = None
    if product.get('brand_id'):
        brand = db.fetch_one("SELECT * FROM pms_brand WHERE id=%s", (product['brand_id'],))

    # 4. 获取评论数据
    comments = db.fetch_all("""
        SELECT * FROM cms_comment 
        WHERE product_id=%s 
        ORDER BY create_time DESC
    """, (product_id,))

    return render_template('product_detail.html',
                           product=product,
                           skus=skus,
                           brand=brand,
                           comments=comments)