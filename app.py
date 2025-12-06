from flask import Flask, redirect, url_for
from config import Config

# 导入所有子系统的 Blueprint
from ums.views import ums_bp
from pms.views import pms_bp
from oms.views import oms_bp
from sms.views import sms_bp
from wms.views import wms_bp
from cms.views import cms_bp
from sys_admin.views import sys_bp

app = Flask(__name__)
app.config.from_object(Config)

# 注册蓝图 (URL前缀区分模块)
app.register_blueprint(ums_bp, url_prefix='/ums')
app.register_blueprint(pms_bp, url_prefix='/pms')
app.register_blueprint(oms_bp, url_prefix='/oms')
app.register_blueprint(sms_bp, url_prefix='/sms')
app.register_blueprint(wms_bp, url_prefix='/wms')
app.register_blueprint(cms_bp, url_prefix='/cms')
app.register_blueprint(sys_bp, url_prefix='/admin')

@app.route('/')
def index():
    # 首页重定向到商品列表
    return redirect(url_for('pms.index'))

if __name__ == '__main__':
    print("系统启动: http://127.0.0.1:8088")
    app.run(host='0.0.0.0', port=8088)