/*
 * B2C商城系统最终版数据库脚本
 * 版本：Final Release 1.0
 * 包含：UMS, PMS, OMS, SMS, WMS, CMS, SYS 七大模块
 */

DROP DATABASE IF EXISTS mall_b2c;
CREATE DATABASE mall_b2c DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE mall_b2c;

-- =======================================================
-- 1. UMS (用户子系统)
-- =======================================================
CREATE TABLE `ums_member_level` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) COMMENT '等级名称',
  `growth_point` INT COMMENT '所需成长值',
  `priviledge_free_freight` TINYINT COMMENT '是否有免邮特权',
  PRIMARY KEY (`id`)
);

CREATE TABLE `ums_member` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `member_level_id` BIGINT COMMENT '会员等级ID',
  `username` VARCHAR(64) UNIQUE COMMENT '用户名',
  `password` VARCHAR(64) COMMENT '密码',
  `nickname` VARCHAR(64) COMMENT '昵称',
  `phone` VARCHAR(20) UNIQUE COMMENT '手机号',
  `status` TINYINT DEFAULT 1 COMMENT '帐号状态:0->禁用；1->启用',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT fk_member_level FOREIGN KEY (member_level_id) REFERENCES ums_member_level(id)
);

CREATE TABLE `ums_member_receive_address` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `member_id` BIGINT COMMENT '会员ID',
  `name` VARCHAR(100) COMMENT '收货人',
  `phone_number` VARCHAR(20) COMMENT '电话',
  `detail_address` VARCHAR(128) COMMENT '详细地址',
  `default_status` TINYINT DEFAULT 0 COMMENT '是否默认',
  PRIMARY KEY (`id`),
  CONSTRAINT fk_addr_member FOREIGN KEY (member_id) REFERENCES ums_member(id) ON DELETE CASCADE
);

-- =======================================================
-- 2. PMS (商品子系统)
-- =======================================================
CREATE TABLE `pms_category` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `parent_id` BIGINT DEFAULT 0 COMMENT '上级ID',
  `name` VARCHAR(64) COMMENT '名称',
  `level` INT COMMENT '层级:0->1级',
  `sort` INT DEFAULT 0,
  PRIMARY KEY (`id`)
);

CREATE TABLE `pms_brand` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) COMMENT '名称',
  `logo` VARCHAR(255) COMMENT 'Logo',
  `product_count` INT DEFAULT 0,
  PRIMARY KEY (`id`)
);

CREATE TABLE `pms_product` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `brand_id` BIGINT COMMENT '品牌ID',
  `category_id` BIGINT COMMENT '分类ID',
  `name` VARCHAR(200) NOT NULL COMMENT '商品名称',
  `pic` VARCHAR(255) COMMENT '主图',
  `product_sn` VARCHAR(64) NOT NULL COMMENT '货号',
  `publish_status` TINYINT DEFAULT 0 COMMENT '上架状态',
  `delete_status` TINYINT DEFAULT 0 COMMENT '删除状态:0->未删;1->已删',
  `price` DECIMAL(10,2) COMMENT '价格',
  `sale` INT DEFAULT 0 COMMENT '销量',
  `description` TEXT COMMENT '详情',
  PRIMARY KEY (`id`),
  CONSTRAINT fk_pro_cat FOREIGN KEY (category_id) REFERENCES pms_category(id),
  CONSTRAINT fk_pro_brand FOREIGN KEY (brand_id) REFERENCES pms_brand(id)
);

CREATE TABLE `pms_sku_stock` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `product_id` BIGINT COMMENT '商品ID',
  `sku_code` VARCHAR(64) NOT NULL COMMENT 'sku编码',
  `price` DECIMAL(10,2) COMMENT '价格',
  `stock` INT DEFAULT 0 COMMENT '库存',
  `sp_data` VARCHAR(500) COMMENT '销售属性JSON',
  PRIMARY KEY (`id`),
  CONSTRAINT fk_sku_pro FOREIGN KEY (product_id) REFERENCES pms_product(id) ON DELETE CASCADE
);

-- =======================================================
-- 3. SMS (营销子系统)
-- =======================================================
CREATE TABLE `sms_coupon` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) COMMENT '名称',
  `amount` DECIMAL(10,2) COMMENT '金额',
  `min_point` DECIMAL(10,2) COMMENT '门槛',
  `end_time` DATETIME COMMENT '结束时间',
  PRIMARY KEY (`id`)
);

CREATE TABLE `sms_coupon_history` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `coupon_id` BIGINT,
  `member_id` BIGINT,
  `use_status` INT DEFAULT 0 COMMENT '0->未使用',
  PRIMARY KEY (`id`),
  CONSTRAINT fk_ch_coupon FOREIGN KEY (coupon_id) REFERENCES sms_coupon(id),
  CONSTRAINT fk_ch_member FOREIGN KEY (member_id) REFERENCES ums_member(id)
);

-- =======================================================
-- 4. OMS (订单与交易子系统)
-- =======================================================
CREATE TABLE `oms_order` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `member_id` BIGINT NOT NULL,
  `order_sn` VARCHAR(64) UNIQUE NOT NULL COMMENT '订单号',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `total_amount` DECIMAL(10,2) COMMENT '总金额',
  `status` INT COMMENT '0->待付款;1->待发货;2->已发货;3->已完成',
  `receiver_name` VARCHAR(100) NOT NULL,
  `receiver_phone` VARCHAR(32) NOT NULL,
  `receiver_detail_address` VARCHAR(200),
  PRIMARY KEY (`id`),
  CONSTRAINT fk_order_member FOREIGN KEY (member_id) REFERENCES ums_member(id)
);

CREATE TABLE `oms_order_item` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `order_id` BIGINT,
  `order_sn` VARCHAR(64),
  `product_id` BIGINT,
  `product_sku_id` BIGINT,
  `product_name` VARCHAR(200),
  `product_price` DECIMAL(10,2),
  `product_quantity` INT,
  `product_attr` VARCHAR(500) COMMENT '购买时属性:颜色尺码',
  PRIMARY KEY (`id`),
  CONSTRAINT fk_item_order FOREIGN KEY (order_id) REFERENCES oms_order(id) ON DELETE CASCADE
  -- 注意：这里不加 product_id 的外键，防止商品删除后订单报错，实现逻辑解耦
);

CREATE TABLE `oms_cart_item` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `member_id` BIGINT,
  `product_id` BIGINT,
  `product_sku_id` BIGINT,
  `quantity` INT,
  `product_attr` VARCHAR(500),
  PRIMARY KEY (`id`),
  CONSTRAINT fk_cart_mem FOREIGN KEY (member_id) REFERENCES ums_member(id) ON DELETE CASCADE,
  CONSTRAINT fk_cart_pro FOREIGN KEY (product_id) REFERENCES pms_product(id) ON DELETE CASCADE
);

CREATE TABLE `oms_order_return_apply` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `order_id` BIGINT,
  `status` INT DEFAULT 0 COMMENT '0->待处理',
  `reason` VARCHAR(200),
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT fk_return_order FOREIGN KEY (order_id) REFERENCES oms_order(id)
);

-- =======================================================
-- 5. WMS (库存与物流)
-- =======================================================
CREATE TABLE `wms_ware_info` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100),
  PRIMARY KEY (`id`)
);

CREATE TABLE `wms_ware_sku` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `sku_id` BIGINT,
  `ware_id` BIGINT,
  `stock` INT,
  PRIMARY KEY (`id`),
  CONSTRAINT fk_wms_sku FOREIGN KEY (sku_id) REFERENCES pms_sku_stock(id),
  CONSTRAINT fk_wms_ware FOREIGN KEY (ware_id) REFERENCES wms_ware_info(id)
);

-- =======================================================
-- 6. CMS (内容)
-- =======================================================
CREATE TABLE `cms_comment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `product_id` BIGINT,
  `member_nick_name` VARCHAR(255),
  `content` TEXT,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT fk_com_pro FOREIGN KEY (product_id) REFERENCES pms_product(id)
);

-- =======================================================
-- 7. SYS (系统后台)
-- =======================================================
CREATE TABLE `sys_role` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) COMMENT '角色名:超级管理员/客服',
  PRIMARY KEY (`id`)
);

CREATE TABLE `sys_admin` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `role_id` BIGINT COMMENT '角色ID',
  `username` VARCHAR(64) UNIQUE,
  `password` VARCHAR(64),
  `nick_name` VARCHAR(100),
  PRIMARY KEY (`id`),
  CONSTRAINT fk_admin_role FOREIGN KEY (role_id) REFERENCES sys_role(id)
);

-- =======================================================
-- 8. 高级特性 (View & Procedure)
-- =======================================================
CREATE OR REPLACE VIEW v_order_detail AS
SELECT o.id, o.order_sn, o.member_id, oi.product_name, oi.product_price
FROM oms_order o JOIN oms_order_item oi ON o.id = oi.order_id;

DELIMITER $$
CREATE PROCEDURE p_daily_sales(IN q_date DATE, OUT total DECIMAL(10,2))
BEGIN
    SELECT IFNULL(SUM(total_amount), 0) INTO total FROM oms_order
    WHERE DATE(create_time) = q_date AND status <> 0;
END $$
DELIMITER ;

-- =======================================================
-- 9. 数据初始化 (Data Init)
-- =======================================================
-- 基础字典
INSERT INTO ums_member_level (name, growth_point) VALUES ('普通会员',0), ('黄金会员',1000);
INSERT INTO pms_brand (name, product_count) VALUES ('Apple', 100), ('小米', 50);
INSERT INTO pms_category (name, level) VALUES ('手机', 0), ('家电', 0);
INSERT INTO sys_role (name) VALUES ('超级管理员'), ('普通客服');
INSERT INTO wms_ware_info (name) VALUES ('北京总仓');

-- 核心业务数据 (确保演示不报错)
INSERT INTO sys_admin (role_id, username, password, nick_name)
VALUES (1, 'admin', '123456', 'SuperAdmin');

INSERT INTO ums_member (member_level_id, username, password, phone, nickname)
VALUES (1, 'test_user', '123456', '13800000000', '测试用户');

INSERT INTO pms_product (brand_id, category_id, name, product_sn, price, stock, pic)
VALUES (1, 1, 'iPhone 15 Pro', 'NO.8888', 7999.00, 100, 'http://img.com/iphone.jpg');

INSERT INTO pms_sku_stock (product_id, sku_code, price, stock, sp_data)
VALUES (1, 'SKU001', 7999.00, 50, '{"color":"黑色"}');

INSERT INTO ums_member_receive_address (member_id, name, phone_number, detail_address, default_status)
VALUES (1, '张三', '13800000000', '北京市海淀区', 1);

-- 结束


USE mall_b2c;

-- 1. 修正后的插入商品语句 (去掉了 stock 字段)
INSERT INTO pms_product (brand_id, category_id, name, product_sn, price, pic)
VALUES (1, 1, 'iPhone 15 Pro', 'NO.8888', 7999.00, 'http://img.com/iphone.jpg');

-- 2. 再次执行插入 SKU 库存 (这次就能成功了，因为 product_id=1 存在了)
INSERT INTO pms_sku_stock (product_id, sku_code, price, stock, sp_data)
VALUES (1, 'SKU001', 7999.00, 50, '{"color":"黑色"}');

INSERT INTO sms_coupon (name, amount, min_point, end_time)
VALUES ('开业大酬宾', 100.00, 500.00, '2025-12-31 23:59:59');


USE mall_b2c;

-- 1. 添加发行量和已领量字段
ALTER TABLE sms_coupon
ADD COLUMN `publish_count` INT DEFAULT 100 COMMENT '发行数量',
ADD COLUMN `receive_count` INT DEFAULT 0 COMMENT '已领取数量';

-- 2. 更新一下之前的测试数据，确保不报错
UPDATE sms_coupon SET publish_count=100, receive_count=0;

-- 3. 再插一条库存很少的券，方便你测试“抢光了”的场景
INSERT INTO sms_coupon (name, amount, min_point, end_time, publish_count, receive_count)
VALUES ('手慢无（测试券）', 50.00, 100.00, '2025-12-31 23:59:59', 2, 0);

USE mall_b2c;

-- 为购物车表补全缺失的字段
ALTER TABLE oms_cart_item
ADD COLUMN price DECIMAL(10,2) COMMENT '添加时价格',
ADD COLUMN product_pic VARCHAR(500) COMMENT '商品图片',
ADD COLUMN product_name VARCHAR(200) COMMENT '商品名称',
ADD COLUMN product_sku_code VARCHAR(200) COMMENT 'SKU条码',
ADD COLUMN create_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间';


USE mall_b2c;

-- 为 WMS 库存表补全锁定库存字段
ALTER TABLE wms_ware_sku
ADD COLUMN stock_locked INT DEFAULT 0 COMMENT '锁定库存(待发货)';

USE mall_b2c;

-- 1. 先清理可能存在的脏数据 (按顺序删除，避免外键报错)
DELETE FROM wms_ware_sku;
DELETE FROM oms_cart_item;
DELETE FROM oms_order_item;
DELETE FROM pms_sku_stock;
DELETE FROM pms_product;
DELETE FROM pms_category;
DELETE FROM pms_brand;

-- 2. 插入分类
INSERT INTO pms_category (id, name, parent_id, level, sort) VALUES
(1, '手机数码', 0, 0, 1),
(2, '家用电器', 0, 0, 2);

-- 3. 插入品牌
INSERT INTO pms_brand (id, name, logo, product_count) VALUES
(1, 'Apple', 'https://img14.360buyimg.com/n1/jfs/t1/202062/12/35560/94467/650cf5eeF67e58428/8a159f518e388273.jpg', 100),
(2, '小米', 'https://img14.360buyimg.com/n1/jfs/t1/157002/26/36465/86266/653b6e80Ff7b44535/5341400626359d9f.jpg', 50);

-- 4. 插入商品 (publish_status=1 代表上架)
-- 注意：这里没有 stock 字段，这是正确的！
INSERT INTO pms_product (id, brand_id, category_id, name, pic, product_sn, publish_status, delete_status, price, sale) VALUES
(1, 1, 1, 'iPhone 15 Pro Max', 'https://img14.360buyimg.com/n1/s450x450_jfs/t1/202062/12/35560/94467/650cf5eeF67e58428/8a159f518e388273.jpg', 'NO.1001', 1, 0, 9999.00, 500),
(2, 2, 1, 'Xiaomi 14 Pro', 'https://img14.360buyimg.com/n1/s450x450_jfs/t1/157002/26/36465/86266/653b6e80Ff7b44535/5341400626359d9f.jpg', 'NO.1002', 1, 0, 4999.00, 1000);

-- 5. 插入 SKU 库存 (库存和价格在这里！)
INSERT INTO pms_sku_stock (product_id, sku_code, price, stock, sp_data) VALUES
(1, '2023001', 9999.00, 100, '黑色钛金属 256G'),
(2, '2023002', 4999.00, 200, '岩石青 12G+256G');

-- 将 iPhone 的图片改为本地路径
UPDATE pms_product
SET pic = '/static/iphone15.jpg'
WHERE id = 1;

USE mall_b2c;

UPDATE pms_product
SET pic = 'https://cdsassets.apple.com/live/7WUAS350/images/tech-specs/iphone-15-pro-max.png'
WHERE id = 1;

USE mall_b2c;

-- 补全优惠券历史表的使用时间字段
ALTER TABLE sms_coupon_history
ADD COLUMN use_time DATETIME DEFAULT NULL COMMENT '使用时间';




USE mall_b2c;

-- 1. 给等级表增加“折扣率”字段
ALTER TABLE ums_member_level
ADD COLUMN discount DECIMAL(10,2) DEFAULT 1.00 COMMENT '折扣率: 1.00=原价, 0.90=九折';

-- 2. 配置等级折扣 (普通不打折，黄金9折，钻石8折)
UPDATE ums_member_level SET discount = 1.00 WHERE name = '普通会员';
UPDATE ums_member_level SET discount = 0.90 WHERE name = '黄金会员';
UPDATE ums_member_level SET discount = 0.80 WHERE name = '钻石会员';

-- 3. 为了方便测试，把我们的测试账号(test_user) 升级为 "黄金会员" (ID=2)
-- 假设 test_user 的 ID 是 1
UPDATE ums_member SET member_level_id = 2 WHERE username = 'test_user';


USE mall_b2c;

-- 为后台管理员表补全状态字段
ALTER TABLE sys_admin
ADD COLUMN status INT DEFAULT 1 COMMENT '帐号状态: 0->禁用; 1->启用';