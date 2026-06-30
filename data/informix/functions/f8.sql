CREATE FUNCTION MAXPURCHASECHANNEL (ckey INT, fromDate INT, toDate INT)
RETURNS VARCHAR(50)
BEGIN
    DEFINE numSalesFromStore INT;
    DEFINE numSalesFromCatalog INT;
    DEFINE numSalesFromWeb INT;
    DEFINE maxChannel VARCHAR(50);

    SELECT COUNT(*) INTO numSalesFromStore
    FROM store_sales_history
    WHERE ss_customer_sk = ckey 
      AND ss_sold_date_sk BETWEEN fromDate AND toDate;

    SELECT COUNT(*) INTO numSalesFromCatalog
    FROM catalog_sales_history
    WHERE cs_bill_customer_sk = ckey 
      AND cs_sold_date_sk BETWEEN fromDate AND toDate;

    SELECT COUNT(*) INTO numSalesFromWeb
    FROM web_sales_history
    WHERE ws_bill_customer_sk = ckey 
      AND ws_sold_date_sk BETWEEN fromDate AND toDate;

    IF numSalesFromStore > numSalesFromCatalog THEN
        LET maxChannel = 'Store';
        IF numSalesFromWeb > numSalesFromStore THEN
            LET maxChannel = 'Web';
        END IF;
    ELSE
        LET maxChannel = 'Catalog';
        IF numSalesFromWeb > numSalesFromCatalog THEN
            LET maxChannel = 'Web';
        END IF;
    END IF;

    RETURN maxChannel;
end;
END FUNCTION;