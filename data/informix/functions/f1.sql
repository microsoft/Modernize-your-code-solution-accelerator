CREATE FUNCTION INCOMEBANDOFMAXBUYCUSTOMER(storeNumber INTEGER)
    RETURNING VARCHAR(50);
   
    DEFINE incomeband INTEGER;
    DEFINE cust       INTEGER;
    DEFINE hhdemo     INTEGER;
    DEFINE cnt        INTEGER;
    DEFINE cLevel     VARCHAR(50);
begin
	
	SELECT ss_customer_sk, c_current_hdemo_sk, COUNT(*) 
        INTO cust, hhdemo, cnt
    FROM store_sales_history, customer
    WHERE ss_store_sk = storeNumber 
      AND c_customer_sk = ss_customer_sk
    GROUP BY ss_customer_sk, c_current_hdemo_sk
    HAVING COUNT(*) = (
        SELECT MAX(cnt) 
        FROM (
            SELECT ss_customer_sk, c_current_hdemo_sk, COUNT(*) AS cnt
            FROM store_sales_history, customer
            WHERE ss_store_sk = storeNumber 
              AND c_customer_sk = ss_customer_sk
            GROUP BY ss_customer_sk, c_current_hdemo_sk
            HAVING ss_customer_sk IS NOT NULL
        ) tbl
    );
	
    SELECT hd_income_band_sk 
        INTO incomeband 
    FROM household_demographics 
    WHERE hd_demo_sk = hhdemo;
   
	IF (incomeband >= 0 AND incomeband <= 3) THEN
	    LET cLevel = 'low';
	ELIF (incomeband >= 4 AND incomeband <= 7) THEN
	    LET cLevel = 'lowerMiddle';
	ELIF (incomeband >= 8 AND incomeband <= 11) THEN
	    LET cLevel = 'upperMiddle';
	ELIF (incomeband >= 12 AND incomeband <= 16) THEN
	    LET cLevel = 'high';
	ELIF (incomeband >= 17 AND incomeband <= 20) THEN
	    LET cLevel = 'affluent';
	END IF;

   
    RETURN cLevel;
END;
END FUNCTION;