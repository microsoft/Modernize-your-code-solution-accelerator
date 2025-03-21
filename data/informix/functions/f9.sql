CREATE FUNCTION maxReturnClass() 
RETURNS CHAR(50)
BEGIN
    DEFINE cnt INT;
    DEFINE cls CHAR(50);
    DEFINE maxClass CHAR(50);
    DEFINE maxReturn INT;

    LET maxReturn = 0;
    LET maxClass = NULL;

    FOREACH cursor_c1 FOR
        SELECT i_class, COUNT(i_class) 
        INTO cls, cnt
        FROM catalog_returns, item
        WHERE i_item_sk = cr_item_sk
        GROUP BY i_class
        
        IF cnt > maxReturn THEN
            LET maxReturn = cnt;
            LET maxClass = cls;
        END IF;
    END FOREACH;

    RETURN maxClass;
END;
end function;