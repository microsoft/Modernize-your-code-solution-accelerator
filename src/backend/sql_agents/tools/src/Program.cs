using System;
using System.Collections.Generic;
using System.IO;
using Microsoft.SqlServer.TransactSql.ScriptDom;
using Newtonsoft.Json;

namespace SqlParserApp
{
    class Program
    {
        static void Main(string[] args)
        {
            string sqlQuery = string.Empty;
            if (args.Length == 0)
            {
                Console.WriteLine("Please provide a SQL query string (--string) or file (--file) as an argument.");
                return;
            }
            if (args[0] == "--file")
            {
                if (args.Length < 2)
                {
                    Console.WriteLine("Please provide a file path after --file.");
                    return;
                }
                string filePath = args[1];
                if (!File.Exists(filePath))
                {
                    Console.WriteLine($"File not found: {filePath}");
                    return;
                }
                sqlQuery = File.ReadAllText(filePath);
            }
            else if (args[0] == "--string")
            {
                sqlQuery = string.Join(" ", args); // Join the array elements into a single string
            }
            else
            {
                Console.WriteLine("Invalid argument. Use --file or --string.");
            }

            IList<ParseError> errors = ParseSqlQuery(sqlQuery);

            var errorList = new List<Dictionary<string, object>>();

            foreach (var error in errors)
            {
                var errorDict = new Dictionary<string, object>
                {
                    { "Line", error.Line },
                    { "Column", error.Column },
                    { "Error", error.Message }
                };
                errorList.Add(errorDict);
            }

            string jsonOutput = JsonConvert.SerializeObject(errorList, Formatting.Indented);
            Console.WriteLine(jsonOutput);
        }

        static IList<ParseError> ParseSqlQuery(string sqlQuery)
        {
            TSql150Parser parser = new TSql150Parser(false);
            IList<ParseError> errors;
            using (TextReader reader = new StringReader(sqlQuery))
            {
                parser.Parse(reader, out errors);
            }
            return errors;
        }
    }
}
