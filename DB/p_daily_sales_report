DELIMITER $$

CREATE PROCEDURE p_daily_sales_report(IN query_date DATE, OUT total_sales DECIMAL(10,2))
BEGIN
    -- 统计指定日期、且状态为已完成(3)的订单总额
    SELECT SUM(total_amount) INTO total_sales
    FROM oms_order
    WHERE DATE(create_time) = query_date AND status = 3;

    -- 如果当天没销量，返回0
    IF total_sales IS NULL THEN
        SET total_sales = 0;
    END IF;
END $$

DELIMITER ;