CREATE PROCEDURE sp_high_value_orders(p_min_value INT)
   RETURNING INT;         -- The procedure will return an integer

   DEFINE order_count INT;

   SELECT COUNT(*)
     INTO order_count
     FROM orders
    WHERE order_total > p_min_value;

   RETURN order_count;
END PROCEDURE;
