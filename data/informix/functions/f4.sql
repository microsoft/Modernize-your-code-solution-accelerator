CREATE FUNCTION GETMANUFACT_SIMPLE(item INT) 
RETURNING CHAR(50);
	DEFINE manufact CHAR(50);

	BEGIN
	    SELECT i_manufact INTO manufact FROM item WHERE i_item_sk = item;
	    RETURN manufact;
	END;
END FUNCTION;