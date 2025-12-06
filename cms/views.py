from flask import Blueprint, request, jsonify, session
from db_helper import DBHelper
import datetime  # 必须导入这个模块，否则会报错

cms_bp = Blueprint('cms', __name__)
db = DBHelper()


# --- 接口：提交商品评价 ---
@cms_bp.route('/add_comment', methods=['POST'])
def add_comment():
    """
    用户提交商品评价
    """
    # 1. 权限校验：必须登录
    if 'user_id' not in session:
        return jsonify({'code': 401, 'msg': '请先登录后发表评价'})

    # 2. 获取前端参数
    product_id = request.form.get('product_id')
    content = request.form.get('content')

    # 获取当前登录用户的昵称
    # 注意：在 UMS 登录时，我们将昵称存入了 session['username']
    member_nick_name = session.get('username')
    if not member_nick_name:
        member_nick_name = '匿名用户'

    # 3. 简单校验
    if not product_id:
        return jsonify({'code': 400, 'msg': '商品参数错误'})
    if not content or len(content.strip()) == 0:
        return jsonify({'code': 400, 'msg': '评价内容不能为空'})

    try:
        # 4. 验证商品是否存在 (可选，防止恶意刷库，保证外键约束安全)
        product = db.fetch_one("SELECT id FROM pms_product WHERE id=%s", (product_id,))
        if not product:
            return jsonify({'code': 404, 'msg': '该商品不存在或已下架'})

        # 5. 写入评价表
        sql = """
            INSERT INTO cms_comment (product_id, member_nick_name, content, create_time)
            VALUES (%s, %s, %s, %s)
        """
        # 获取当前时间
        create_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        db.execute_update(sql, (product_id, member_nick_name, content, create_time))

        return jsonify({'code': 200, 'msg': '评价发表成功'})

    except Exception as e:
        print(f"CMS Error: {e}")  # 在后台打印错误日志，方便调试
        return jsonify({'code': 500, 'msg': '服务器内部错误，请稍后再试'})


# --- 接口：删除评价 (预留给管理员功能) ---
@cms_bp.route('/delete_comment', methods=['POST'])
def delete_comment():
    """
    删除评价
    """
    comment_id = request.form.get('comment_id')
    if not comment_id:
        return jsonify({'code': 400, 'msg': '参数缺失'})

    try:
        sql = "DELETE FROM cms_comment WHERE id=%s"
        rows = db.execute_update(sql, (comment_id,))

        if rows > 0:
            return jsonify({'code': 200, 'msg': '删除成功'})
        else:
            return jsonify({'code': 404, 'msg': '评价不存在'})

    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


# --- 接口：API获取评价 (备用) ---
@cms_bp.route('/api/list')
def api_list_reviews():
    """
    如果前端需要通过Ajax异步刷新评价列表，可调用此接口
    """
    product_id = request.args.get('product_id')
    sql = "SELECT * FROM cms_comment WHERE product_id=%s ORDER BY create_time DESC"
    data = db.fetch_all(sql, (product_id,))
    # 处理时间对象转字符串，防止json序列化报错
    for item in data:
        if isinstance(item['create_time'], datetime.datetime):
            item['create_time'] = item['create_time'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'code': 200, 'data': data})