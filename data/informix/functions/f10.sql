CREATE FUNCTION wealth_shipCostCorrelation_cat() 
RETURNS CHAR(30)
DEFINE numStates INT;

BEGIN
	
	SELECT ca.ca_state
	FROM catalog_sales_history csh
	JOIN customer_address ca ON csh.cs_bill_customer_sk = ca.ca_address_sk
	WHERE ca.ca_state IS NOT NULL
	GROUP BY ca.ca_state
	ORDER BY SUM(cs_ext_ship_cost) DESC
	LIMIT 5
	into temp top_ship_cost_states;

	SELECT ca.ca_state
	FROM customer c
	JOIN household_demographics hd ON c.c_current_hdemo_sk = hd.hd_demo_sk
	JOIN customer_address ca ON c.c_current_addr_sk = ca.ca_address_sk
	WHERE hd.hd_income_band_sk >= 15 
	AND ca.ca_state IS NOT NULL
	GROUP BY ca.ca_state
	ORDER BY COUNT(*) DESC
	LIMIT 5
	into temp top_high_income_states;
	
	SELECT COUNT(*) INTO numStates 
	FROM top_ship_cost_states scs
	JOIN top_high_income_states hics ON scs.ca_state = hics.ca_state;
	
	IF (numStates >= 4) THEN
	    RETURN 'highly correlated';
	ELIF (numStates >= 2 AND numStates <= 3) THEN
	    RETURN 'somewhat correlated';
	ELSE
	    RETURN 'no correlation';
	END IF;
	
	RETURN 'error';
end;
END FUNCTION;