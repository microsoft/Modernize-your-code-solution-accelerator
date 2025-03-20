SELECT c.customer_id,
       c.customer_name,
       o.order_id,
       o.order_date
FROM customer c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
ORDER BY c.customer_name;
