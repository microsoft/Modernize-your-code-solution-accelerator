SELECT o.order_id,
       o.customer_id,
       (
         SELECT ISNULL(SUM(ob.order_total), 0)
         FROM orders_backup ob
         WHERE ob.customer_id = o.customer_id
       ) AS backup_order_total
FROM orders o;
