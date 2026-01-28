CREATE PROCEDURE sp_high_value_orders
    @min_value INT,
    @order_count INT OUTPUT
AS
BEGIN
    SELECT @order_count = COUNT(*)
    FROM orders
    WHERE order_total > @min_value;
END;
