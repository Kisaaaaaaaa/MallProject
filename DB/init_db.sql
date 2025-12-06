CREATE DATABASE IF NOT EXISTS mall_b2c DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE mall_b2c;

--子系统1：子系统 1：用户与权限子系统 (UMS - User Management System)
-- 1. 用户表
CREATE TABLE `ums_member` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(64) COMMENT '用户名',
  `password` VARCHAR(64) COMMENT '加密密码',
  `phone` VARCHAR(20) COMMENT '手机号',
  `nickname` VARCHAR(64) COMMENT '昵称',
  `integration` INT DEFAULT 0 COMMENT '积分',
  `growth` INT DEFAULT 0 COMMENT '成长值',
  `member_level_id` BIGINT COMMENT '会员等级ID',
  `status` TINYINT DEFAULT 1 COMMENT '帐号启用状态:0->禁用；1->启用',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_username` (`username`),
  UNIQUE KEY `idx_phone` (`phone`)
) COMMENT='会员表';

-- 2. 会员等级表
CREATE TABLE `ums_member_level` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) COMMENT '等级名称',
  `growth_point` INT COMMENT '所需成长值',
  `priviledge_free_freight` TINYINT COMMENT '是否有免邮特权',
  PRIMARY KEY (`id`)
) COMMENT='会员等级表';

-- 3. 收货地址表
CREATE TABLE `ums_member_receive_address` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `member_id` BIGINT COMMENT '会员ID',
  `name` VARCHAR(100) COMMENT '收货人名称',
  `phone_number` VARCHAR(20) COMMENT '收货人电话',
  `province` VARCHAR(100) COMMENT '省份/直辖市',
  `city` VARCHAR(100) COMMENT '城市',
  `region` VARCHAR(100) COMMENT '区',
  `detail_address` VARCHAR(128) COMMENT '详细地址(街道)',
  `default_status` TINYINT DEFAULT 0 COMMENT '是否为默认',
  PRIMARY KEY (`id`)
) COMMENT='会员收货地址表';

--子系统 2：商品与类目子系统 (PMS - Product Management System)
-- 1. 商品分类表 (核心自关联表)
CREATE TABLE `pms_category` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `parent_id` BIGINT DEFAULT 0 COMMENT '上级分类的编号：0表示一级分类',
  `name` VARCHAR(64) COMMENT '分类名称',
  `level` INT COMMENT '分类级别：0->1级；1->2级',
  `sort` INT DEFAULT 0 COMMENT '排序字段',
  PRIMARY KEY (`id`)
) COMMENT='商品分类表';

-- 2. 商品主表 (SPU)
CREATE TABLE `pms_product` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `brand_id` BIGINT COMMENT '品牌ID',
  `category_id` BIGINT COMMENT '分类ID',
  `name` VARCHAR(200) NOT NULL COMMENT '商品名称',
  `pic` VARCHAR(255) COMMENT '主图URL',
  `product_sn` VARCHAR(64) NOT NULL COMMENT '货号',
  `publish_status` TINYINT DEFAULT 0 COMMENT '上架状态：0->下架；1->上架',
  `price` DECIMAL(10,2) COMMENT '市场价',
  `sale` INT DEFAULT 0 COMMENT '销量',
  `description` TEXT COMMENT '商品描述',
  PRIMARY KEY (`id`)
) COMMENT='商品信息表';

-- 3. 商品库存单位表 (SKU - 实际售卖的单品)
CREATE TABLE `pms_sku_stock` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `product_id` BIGINT COMMENT '商品ID',
  `sku_code` VARCHAR(64) NOT NULL COMMENT 'sku编码',
  `price` DECIMAL(10,2) COMMENT '销售价格',
  `stock` INT DEFAULT 0 COMMENT '库存',
  `sp_data` VARCHAR(500) COMMENT '销售属性JSON，如：[{"key":"颜色","value":"黑色"},{"key":"容量","value":"128G"}]',
  PRIMARY KEY (`id`)
) COMMENT='sku库存表';

DROP TABLE IF EXISTS `pms_brand`;
CREATE TABLE `pms_brand` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) DEFAULT NULL COMMENT '名称',
  `first_letter` VARCHAR(8) DEFAULT NULL COMMENT '首字母',
  `sort` INT DEFAULT 0 COMMENT '排序',
  `factory_status` INT DEFAULT 0 COMMENT '是否为品牌制造商：0->不是；1->是',
  `show_status` INT DEFAULT 0 COMMENT '是否显示',
  `product_count` INT DEFAULT 0 COMMENT '产品数量',
  `product_comment_count` INT DEFAULT 0 COMMENT '产品评论数量',
  `logo` VARCHAR(255) DEFAULT NULL COMMENT '品牌logo',
  `big_pic` VARCHAR(255) DEFAULT NULL COMMENT '专区大图',
  PRIMARY KEY (`id`)
) COMMENT='品牌表';


--子系统 3：营销与活动子系统 (SMS - Sales Management System)
-- 1. 优惠券表
CREATE TABLE `sms_coupon` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `type` INT COMMENT '优惠券类型；0->全场赠券；1->会员赠券；2->购物赠券；3->注册赠券',
  `name` VARCHAR(100) COMMENT '名称',
  `amount` DECIMAL(10,2) COMMENT '金额',
  `min_point` DECIMAL(10,2) COMMENT '使用门槛；0表示无门槛',
  `start_time` DATETIME COMMENT '开始时间',
  `end_time` DATETIME COMMENT '结束时间',
  `publish_count` INT COMMENT '发行数量',
  `receive_count` INT COMMENT '领取数量',
  PRIMARY KEY (`id`)
) COMMENT='优惠券表';

-- 2. 优惠券领取历史表 (连接 Member 和 Coupon)
CREATE TABLE `sms_coupon_history` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `coupon_id` BIGINT COMMENT '优惠券ID',
  `member_id` BIGINT COMMENT '会员ID',
  `coupon_code` VARCHAR(64) COMMENT '优惠券码',
  `get_type` INT COMMENT '获取类型：0->后台赠送；1->主动获取',
  `create_time` DATETIME COMMENT '领取时间',
  `use_status` INT DEFAULT 0 COMMENT '使用状态：0->未使用；1->已使用；2->已过期',
  `use_time` DATETIME COMMENT '使用时间',
  `order_id` BIGINT COMMENT '订单ID',
  PRIMARY KEY (`id`)
) COMMENT='优惠券领取记录表';

--子系统 4：订单与交易子系统 (OMS - Order Management System)
-- 1. 订单主表
CREATE TABLE `oms_order` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `member_id` BIGINT NOT NULL COMMENT '会员ID',
  `order_sn` VARCHAR(64) NOT NULL COMMENT '订单编号',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
  `member_username` VARCHAR(64) COMMENT '用户帐号',
  `total_amount` DECIMAL(10,2) COMMENT '订单总金额',
  `pay_amount` DECIMAL(10,2) COMMENT '应付金额（实际支付金额）',
  `pay_type` INT COMMENT '支付方式：0->未支付；1->支付宝；2->微信',
  `status` INT COMMENT '订单状态：0->待付款；1->待发货；2->已发货；3->已完成；4->已关闭',
  `receiver_name` VARCHAR(100) NOT NULL COMMENT '收货人姓名',
  `receiver_phone` VARCHAR(32) NOT NULL COMMENT '收货人电话',
  `receiver_detail_address` VARCHAR(200) COMMENT '详细地址',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_order_sn` (`order_sn`)
) COMMENT='订单表';

-- 2. 订单包含的商品列表 (快照表)
CREATE TABLE `oms_order_item` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `order_id` BIGINT COMMENT '订单ID',
  `order_sn` VARCHAR(64) COMMENT '订单编号',
  `product_id` BIGINT COMMENT '商品ID',
  `product_pic` VARCHAR(500) COMMENT '商品图片',
  `product_name` VARCHAR(200) COMMENT '商品名称',
  `product_sn` VARCHAR(50) COMMENT '商品货号',
  `product_price` DECIMAL(10,2) COMMENT '销售价格(下单时价格)',
  `product_quantity` INT COMMENT '购买数量',
  `product_sku_id` BIGINT COMMENT '商品sku编号',
  `product_sku_code` VARCHAR(50) COMMENT '商品sku条码',
  PRIMARY KEY (`id`)
) COMMENT='订单详情表';

CREATE TABLE `oms_cart_item` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `product_id` BIGINT COMMENT '商品ID',
  `product_sku_id` BIGINT COMMENT 'SKU ID',
  `member_id` BIGINT COMMENT '会员ID',
  `quantity` INT COMMENT '购买数量',
  `price` DECIMAL(10,2) COMMENT '添加购物车时的价格',
  `product_pic` VARCHAR(500) COMMENT '商品图片',
  `product_name` VARCHAR(200) COMMENT '商品名称',
  `product_sku_code` VARCHAR(200) COMMENT '商品sku条码',
  `member_nickname` VARCHAR(500) COMMENT '会员昵称',
  `create_date` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `product_attr` VARCHAR(500) COMMENT '销售属性JSON',
  PRIMARY KEY (`id`)
) COMMENT='购物车表';

--子系统 5：库存与供应链子系统 (WMS - Warehouse Management System)
-- 1. 仓库信息表
CREATE TABLE `wms_ware_info` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) COMMENT '仓库名',
  `address` VARCHAR(255) COMMENT '仓库地址',
  `areacode` VARCHAR(20) COMMENT '区域编码',
  PRIMARY KEY (`id`)
) COMMENT='仓库信息表';

-- 2. 仓库商品库存表
CREATE TABLE `wms_ware_sku` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `sku_id` BIGINT COMMENT 'sku_id',
  `ware_id` BIGINT COMMENT '仓库id',
  `stock` INT COMMENT '库存数',
  `stock_locked` INT DEFAULT 0 COMMENT '锁定库存(如下单未支付)',
  `sku_name` VARCHAR(200) COMMENT 'sku_name(冗余字段)',
  PRIMARY KEY (`id`)
) COMMENT='商品库存分布表';

--子系统 6：内容与评价子系统 (CMS - Content Management System)
-- 1. 商品评价表
CREATE TABLE `cms_comment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `product_id` BIGINT COMMENT '商品ID',
  `member_nick_name` VARCHAR(255) COMMENT '会员昵称',
  `product_name` VARCHAR(255) COMMENT '商品名称',
  `star` INT(3) COMMENT '评价星数：0->5',
  `content` TEXT COMMENT '评价内容',
  `pics` VARCHAR(1000) COMMENT '上传图片地址，以逗号隔开',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) COMMENT='商品评价表';

-- 2. 推荐专题表 (首页广告/活动)
CREATE TABLE `cms_subject` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `category_id` BIGINT COMMENT '分类',
  `title` VARCHAR(100) COMMENT '专题标题',
  `pic` VARCHAR(500) COMMENT '专题主图',
  `description` TEXT COMMENT '内容',
  `create_time` DATETIME COMMENT '创建时间',
  PRIMARY KEY (`id`)
) COMMENT='专题推荐表';

-- 1. 插入测试用户 (密码是 123456)
INSERT INTO ums_member (username, password, phone, nickname)
VALUES ('admin', '123456', '13800138000', '测试管理员');

-- 2. 插入测试分类
INSERT INTO pms_category (name, level, sort)
VALUES ('手机数码', 0, 1);

-- 3. 插入测试商品 (注意：这里补全了 product_sn)
-- 假设刚插入的分类ID是1
INSERT INTO pms_product (brand_id, category_id, name, pic, product_sn, publish_status, price, sale)
VALUES (0, 1, 'iPhone 15 Pro', 'http://dummyimage.com/200x200', 'NO.1001', 1, 7999.00, 0);

-- 4. 插入测试SKU库存 (注意：这里补全了 sku_code)
-- 假设刚插入的商品ID是1
INSERT INTO pms_sku_stock (product_id, sku_code, price, stock, sp_data)
VALUES (1, '20231204001', 7999.00, 100, '[{"key":"颜色","value":"钛金属"}]');

-- 5. 插入测试收货地址 (为了让下单流程不报错)
-- 假设刚插入的用户ID是1
INSERT INTO ums_member_receive_address (member_id, name, phone_number, default_status, detail_address)
VALUES (1, '张三', '13800138000', 1, '北京市朝阳区三环路');

USE mall_b2c;

-- 1. 初始化会员等级 (必须先有等级，才能创建会员)
INSERT INTO ums_member_level (name, growth_point, priviledge_free_freight)
VALUES ('普通会员', 0, 0), ('黄金会员', 1000, 1), ('钻石会员', 5000, 1);

-- 2. 初始化品牌数据 (必须先有品牌，才能创建商品，如果brand_id=0则无需此步，但为了规范建议加上)
INSERT INTO pms_brand (name, first_letter, sort, factory_status, show_status, product_count, product_comment_count, logo, big_pic)
VALUES ('Apple', 'A', 0, 1, 1, 100, 100, 'apple_logo.png', ''),
       ('小米', 'X', 1, 1, 1, 100, 100, 'mi_logo.png', '');

-- 3. 初始化仓库信息 (WMS)
INSERT INTO wms_ware_info (name, address, areacode)
VALUES ('北京一号仓', '北京市大兴区', '100000'), ('上海二号仓', '上海市浦东新区', '200000');




-----------补充外键约束
USE mall_b2c;

-- ==========================================
-- 1. 用户体系关联 (UMS)
-- ==========================================

-- 关联：收货地址 -> 用户
-- 含义：一个地址必须属于一个存在的用户
ALTER TABLE ums_member_receive_address
ADD CONSTRAINT fk_address_member
FOREIGN KEY (member_id) REFERENCES ums_member(id)
ON DELETE CASCADE; -- 如果用户被删，地址自动全删

-- 关联：用户 -> 会员等级
-- 含义：用户的等级ID必须在等级表里存在
ALTER TABLE ums_member
ADD CONSTRAINT fk_member_level
FOREIGN KEY (member_level_id) REFERENCES ums_member_level(id);


-- ==========================================
-- 2. 商品体系关联 (PMS)
-- ==========================================

-- 关联：商品 -> 分类
-- 含义：商品必须属于一个有效的分类
ALTER TABLE pms_product
ADD CONSTRAINT fk_product_category
FOREIGN KEY (category_id) REFERENCES pms_category(id);

-- 关联：SKU库存 -> 商品
-- 含义：库存单品必须属于一个商品主表
ALTER TABLE pms_sku_stock
ADD CONSTRAINT fk_sku_product
FOREIGN KEY (product_id) REFERENCES pms_product(id)
ON DELETE CASCADE; -- 如果商品删了，SKU自动全删


-- ==========================================
-- 3. 订单体系关联 (OMS) - 最核心的部分
-- ==========================================

-- 关联：订单 -> 用户
-- 含义：订单必须属于一个用户
ALTER TABLE oms_order
ADD CONSTRAINT fk_order_member
FOREIGN KEY (member_id) REFERENCES ums_member(id);

-- 关联：订单详情 -> 订单
-- 含义：详情条目必须属于一个订单
ALTER TABLE oms_order_item
ADD CONSTRAINT fk_item_order
FOREIGN KEY (order_id) REFERENCES oms_order(id)
ON DELETE CASCADE;

-- 关联：订单详情 -> 商品 (可选，建议加)
-- 含义：订单里的商品ID必须是商品表里有的
ALTER TABLE oms_order_item
ADD CONSTRAINT fk_item_product
FOREIGN KEY (product_id) REFERENCES pms_product(id);


-- ==========================================
-- 4. 营销体系关联 (SMS)
-- ==========================================

-- 关联：领券记录 -> 优惠券
ALTER TABLE sms_coupon_history
ADD CONSTRAINT fk_history_coupon
FOREIGN KEY (coupon_id) REFERENCES sms_coupon(id);

-- 关联：领券记录 -> 用户
ALTER TABLE sms_coupon_history
ADD CONSTRAINT fk_history_member
FOREIGN KEY (member_id) REFERENCES ums_member(id);


-- ==========================================
-- 5. 评价与仓储关联
-- ==========================================

-- 关联：评价 -> 商品
ALTER TABLE cms_comment
ADD CONSTRAINT fk_comment_product
FOREIGN KEY (product_id) REFERENCES pms_product(id);

-- 关联：仓库库存 -> SKU
ALTER TABLE wms_ware_sku
ADD CONSTRAINT fk_ware_sku
FOREIGN KEY (sku_id) REFERENCES pms_sku_stock(id);

-- 关联：仓库库存 -> 仓库信息
ALTER TABLE wms_ware_sku
ADD CONSTRAINT fk_ware_info
FOREIGN KEY (ware_id) REFERENCES wms_ware_info(id);


ALTER TABLE oms_cart_item
ADD CONSTRAINT fk_cart_member
FOREIGN KEY (member_id) REFERENCES ums_member(id) ON DELETE CASCADE;

ALTER TABLE oms_cart_item
ADD CONSTRAINT fk_cart_product
FOREIGN KEY (product_id) REFERENCES pms_product(id) ON DELETE CASCADE;

-- 将所有名字包含 'iPhone' 的商品，品牌归属为 'Apple' (假设 Apple 的 ID 为 1)
-- 请先确认 select * from pms_brand where name='Apple' 的 id 是多少，如果是 1 则如下：
UPDATE pms_product SET brand_id = 1 WHERE name LIKE '%iPhone%';


USE mall_b2c;

CREATE TABLE `sys_admin` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(64) COMMENT '用户名',
  `password` VARCHAR(64) COMMENT '密码',
  `icon` VARCHAR(500) COMMENT '头像',
  `email` VARCHAR(100) COMMENT '邮箱',
  `nick_name` VARCHAR(100) COMMENT '昵称',
  `note` VARCHAR(500) COMMENT '备注信息',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `login_time` DATETIME COMMENT '最后登录时间',
  `status` INT DEFAULT 1 COMMENT '帐号启用状态：0->禁用；1->启用',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_admin_username` (`username`)
) COMMENT='后台管理员表';

-- 初始化一个超级管理员
INSERT INTO sys_admin (username, password, nick_name)
VALUES ('admin', '123456', '系统超级管理员');


CREATE TABLE `oms_order_return_apply` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `order_id` BIGINT COMMENT '订单id',
  `order_sn` VARCHAR(64) COMMENT '订单编号',
  `product_id` BIGINT COMMENT '退货商品id',
  `member_username` VARCHAR(64) COMMENT '会员用户名',
  `return_amount` DECIMAL(10,2) COMMENT '退款金额',
  `return_name` VARCHAR(100) COMMENT '退货人姓名',
  `return_phone` VARCHAR(100) COMMENT '退货人电话',
  `status` INT COMMENT '申请状态：0->待处理；1->退货中；2->已完成；3->已拒绝',
  `handle_time` DATETIME COMMENT '处理时间',
  `product_pic` VARCHAR(500) COMMENT '商品图片',
  `product_name` VARCHAR(200) COMMENT '商品名称',
  `reason` VARCHAR(200) COMMENT '退货原因',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
  PRIMARY KEY (`id`)
) COMMENT='订单退货申请表';

-- 建立外键关联，保证数据安全
ALTER TABLE oms_order_return_apply
ADD CONSTRAINT fk_return_order
FOREIGN KEY (order_id) REFERENCES oms_order(id);