DEFINE order_count INT;

EXECUTE PROCEDURE sp_high_value_orders(1000) INTO order_count;
