CREATE FUNCTION increase_in_web_spending(cust_sk INT)
RETURNS DECIMAL(18,2)
DEFINE spending1 DECIMAL(18,2);
DEFINE spending2 DECIMAL(18,2);
DEFINE increase DECIMAL(18,2);

BEGIN
    LET spending1 = 0;
    LET spending2 = 0;
    LET increase = 0;

    -- Get total spending for the year 2001
    SELECT COALESCE(SUM(ws_net_paid_inc_ship_tax), 0) 
    INTO spending1
    FROM web_sales_history wsh, date_dim dd
    WHERE dd.d_date_sk = wsh.ws_sold_date_sk
      AND dd.d_year = 2001
      AND wsh.ws_bill_customer_sk = cust_sk;

    -- Get total spending for the year 2000
    SELECT COALESCE(SUM(ws_net_paid_inc_ship_tax), 0) 
    INTO spending2
    FROM web_sales_history wsh, date_dim dd
    WHERE dd.d_date_sk = wsh.ws_sold_date_sk
      AND dd.d_year = 2000
      AND wsh.ws_bill_customer_sk = cust_sk;

    -- Check if spending increased or not
    IF spending1 < spending2 THEN
        RETURN -1;
    ELSE
        LET increase = spending1 - spending2;
    END IF;

    RETURN increase;
END;
end function;