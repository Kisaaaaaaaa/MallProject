CREATE OR REPLACE VIEW v_order_detail AS
SELECT
    o.id AS order_id,
    o.order_sn,
    o.create_time,
    o.status,
    o.member_username,
    oi.product_name,
    oi.product_price,
    oi.product_quantity,
    oi.product_price * oi.product_quantity AS item_total_amount
FROM oms_order o
JOIN oms_order_item oi ON o.id = oi.order_id;