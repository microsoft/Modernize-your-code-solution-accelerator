DECLARE @order_count INT;

EXEC sp_high_value_orders
    @min_value = 1000,
    @order_count = @order_count OUTPUT;
