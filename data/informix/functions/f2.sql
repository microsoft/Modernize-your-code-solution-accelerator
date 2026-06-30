CREATE FUNCTION GENRANDOMINT(lower INT, upper INT, rand FLOAT)
RETURNING INT;
    DEFINE result INT;
    DEFINE range INT;

    LET range = upper - lower + 1;
    LET result = FLOOR(rand * range + lower);
    RETURN result;
END FUNCTION;