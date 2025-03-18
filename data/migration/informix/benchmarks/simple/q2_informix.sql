-- Group by customer_id and the first 3 characters of customer_name
SELECT customer_id,
       SUBSTR(customer_name, 1, 3) AS short_name,
       COUNT(*) AS total_orders
FROM orders
GROUP BY customer_id, SUBSTR(customer_name, 1, 3);
