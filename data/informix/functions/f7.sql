CREATE FUNCTION A_PROMOVSNOPROMOITEMS (givenYear INT) 
RETURNS LVARCHAR
DEFINE promoCountWeb INT;
DEFINE noPromoCountWeb INT;
DEFINE promoCountCatalog INT;
DEFINE noPromoCountCatalog INT;
DEFINE promoCountStore INT;
DEFINE noPromoCountStore INT;
DEFINE ratioWeb DECIMAL(10,2);
DEFINE ratioCatalog DECIMAL(10,2);
DEFINE ratioStore DECIMAL(10,2);
DEFINE maxRatio LVARCHAR;

BEGIN
    SELECT SUM(t1.cnt) INTO promoCountWeb
    FROM (
        SELECT ws_item_sk, ws_promo_sk, COUNT(*) AS cnt
        FROM web_sales_history, promotion, date_dim
        WHERE ws_sold_date_sk = d_date_sk
          AND d_year = givenYear
          AND ws_promo_sk = p_promo_sk
          AND (p_channel_email='Y' OR p_channel_catalog='Y' OR p_channel_dmail='Y')
        GROUP BY ws_item_sk, ws_promo_sk
    ) AS t1;

    SELECT SUM(t1.cnt) INTO noPromoCountWeb
    FROM (
        SELECT ws_item_sk, ws_promo_sk, COUNT(*) AS cnt
        FROM web_sales_history, promotion, date_dim
        WHERE ws_sold_date_sk = d_date_sk
          AND d_year = givenYear
          AND ws_promo_sk = p_promo_sk
          AND p_channel_email='N' AND p_channel_catalog='N' AND p_channel_dmail='N'
        GROUP BY ws_item_sk, ws_promo_sk
    ) AS t1;

    LET ratioWeb = promoCountWeb / NULLIF(noPromoCountWeb, 0);

    SELECT SUM(t1.cnt) INTO promoCountCatalog
    FROM (
        SELECT cs_item_sk, cs_promo_sk, COUNT(*) AS cnt
        FROM catalog_sales_history, promotion, date_dim
        WHERE cs_sold_date_sk = d_date_sk
          AND d_year = givenYear
          AND cs_promo_sk = p_promo_sk
          AND (p_channel_email='Y' OR p_channel_catalog='Y' OR p_channel_dmail='Y')
        GROUP BY cs_item_sk, cs_promo_sk
    ) AS t1;

    SELECT SUM(t1.cnt) INTO noPromoCountCatalog
    FROM (
        SELECT cs_item_sk, cs_promo_sk, COUNT(*) AS cnt
        FROM catalog_sales_history, promotion, date_dim
        WHERE cs_sold_date_sk = d_date_sk
          AND d_year = givenYear
          AND cs_promo_sk = p_promo_sk
          AND p_channel_email='N' AND p_channel_catalog='N' AND p_channel_dmail='N'
        GROUP BY cs_item_sk, cs_promo_sk
    ) AS t1;

    LET ratioCatalog = promoCountCatalog / NULLIF(noPromoCountCatalog, 0);

    SELECT SUM(t1.cnt) INTO promoCountStore
    FROM (
        SELECT ss_item_sk, ss_promo_sk, COUNT(*) AS cnt
        FROM store_sales_history, promotion, date_dim
        WHERE ss_sold_date_sk = d_date_sk
          AND d_year = givenYear
          AND ss_promo_sk = p_promo_sk
          AND (p_channel_email='Y' OR p_channel_catalog='Y' OR p_channel_dmail='Y')
        GROUP BY ss_item_sk, ss_promo_sk
    ) AS t1;

    SELECT SUM(t1.cnt) INTO noPromoCountStore
    FROM (
        SELECT ss_item_sk, ss_promo_sk, COUNT(*) AS cnt
        FROM store_sales_history, promotion, date_dim
        WHERE ss_sold_date_sk = d_date_sk
          AND d_year = givenYear
          AND ss_promo_sk = p_promo_sk
          AND p_channel_email='N' AND p_channel_catalog='N' AND p_channel_dmail='N'
        GROUP BY ss_item_sk, ss_promo_sk
    ) AS t1;

    LET ratioStore = promoCountStore / NULLIF(noPromoCountStore, 0);

    IF (ratioWeb > ratioCatalog AND ratioWeb > ratioStore) THEN
        LET maxRatio = 'Web';
    ELIF (ratioCatalog > ratioWeb AND ratioCatalog > ratioStore) THEN
        LET maxRatio = 'Catalog';
    ELSE
        LET maxRatio = 'Store';
    END IF;

    RETURN maxRatio;

END;
end function;