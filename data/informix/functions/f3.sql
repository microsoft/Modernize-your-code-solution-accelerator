CREATE FUNCTION A_GETMANUFACT_COMPLEX(item INT)
RETURNING CHAR(50);
    DEFINE man CHAR(50);
    DEFINE cnt1 INT;
    DEFINE cnt2 INT;

    LET man = '';

    SELECT COUNT(*) INTO cnt1
    FROM store_sales_history s, date_dim d
    WHERE s.ss_item_sk = item 
      AND d.d_date_sk = s.ss_sold_date_sk 
      AND d.d_year = 2003;

    SELECT COUNT(*) INTO cnt2
    FROM catalog_sales_history c, date_dim d
    WHERE c.cs_item_sk = item 
      AND d.d_date_sk = c.cs_sold_date_sk 
      AND d.d_year = 2003;

    IF cnt1 > 0 AND cnt2 > 0 THEN
        SELECT i_manufact INTO man 
        FROM item 
        WHERE i_item_sk = item;
    ELSE
        LET man = 'outdated item';
    END IF;

    RETURN man;
END FUNCTION;