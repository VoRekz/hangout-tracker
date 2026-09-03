import os
import json

base_dir = os.path.abspath('.')
pbip_path = os.path.join(base_dir, 'Hangout_Dashboard.pbip')
report_dir = os.path.join(base_dir, 'Hangout_Dashboard.Report')
model_dir = os.path.join(base_dir, 'Hangout_Dashboard.SemanticModel')

os.makedirs(report_dir, exist_ok=True)
os.makedirs(model_dir, exist_ok=True)

# 1. PBIP file
pbip_data = {
    'version': '1.0',
    'artifacts': [
        {
            'report': {
                'path': 'Hangout_Dashboard.Report'
            }
        }
    ],
    'settings': {
        'enableAutoRecovery': True
    }
}
with open(pbip_path, 'w', encoding='utf-8') as f:
    json.dump(pbip_data, f, indent=2)

# 2. Report definition.pbir
pbir_data = {
    'version': '1.0',
    'datasetReference': {
        'byPath': {
            'path': '../Hangout_Dashboard.SemanticModel'
        }
    }
}
with open(os.path.join(report_dir, 'definition.pbir'), 'w', encoding='utf-8') as f:
    json.dump(pbir_data, f, indent=2)

# 3. Report report.json
report_json_data = {
    'config': json.dumps({
        'version': '5.53',
        'themeCollection': {
            'baseTheme': {
                'name': 'CY24SU06',
                'version': '5.53',
                'type': 2
            }
        }
    }),
    'layoutOptimization': 0
}
with open(os.path.join(report_dir, 'report.json'), 'w', encoding='utf-8') as f:
    json.dump(report_json_data, f, indent=2)

# 4. Semantic Model definition.pbism
pbism_data = {
    'version': '1.0'
}
with open(os.path.join(model_dir, 'definition.pbism'), 'w', encoding='utf-8') as f:
    json.dump(pbism_data, f, indent=2)

server = 'kdicljj-hs69473.snowflakecomputing.com'
warehouse = 'COMPUTE_WH'

def make_m_expr(table_name):
    return [
        'let',
        f'    Source = Snowflake.Databases("{server}", "{warehouse}", [Role="ACCOUNTADMIN"]),',
        '    HangoutTracker_Database = Source{[Name="HANGOUTTRACKER",Kind="Database"]}[Data],',
        '    CORE_Schema = HangoutTracker_Database{[Name="CORE",Kind="Schema"]}[Data],',
        f'    Table_Data = CORE_Schema{{[Name="{table_name}",Kind="Table"]}}[Data]',
        'in',
        '    Table_Data'
    ]

model_bim = {
    'name': 'Hangout_Dashboard',
    'compatibilityLevel': 1567,
    'model': {
        'culture': 'en-US',
        'dataAccessOptions': {
            'legacyRedirects': True,
            'returnErrorValuesAsNull': True
        },
        'defaultPowerBIDataSourceVersion': 'powerBI_V3',
        'sourceQueryCulture': 'en-US',
        'tables': [
            {
                'name': 'PEOPLE',
                'columns': [
                    {'name': 'PERSONID', 'dataType': 'int64', 'sourceColumn': 'PERSONID', 'isNullable': False},
                    {'name': 'NAME', 'dataType': 'string', 'sourceColumn': 'NAME'}
                ],
                'partitions': [
                    {
                        'name': 'PEOPLE-Partition',
                        'mode': 'import',
                        'source': {
                            'type': 'm',
                            'expression': make_m_expr('PEOPLE')
                        }
                    }
                ]
            },
            {
                'name': 'EVENTS',
                'columns': [
                    {'name': 'EVENTID', 'dataType': 'int64', 'sourceColumn': 'EVENTID', 'isNullable': False},
                    {'name': 'EVENTDATE', 'dataType': 'dateTime', 'sourceColumn': 'EVENTDATE', 'formatString': 'yyyy-mm-dd'},
                    {'name': 'LOCATION', 'dataType': 'string', 'sourceColumn': 'LOCATION'},
                    {'name': 'ADDRESS', 'dataType': 'string', 'sourceColumn': 'ADDRESS', 'dataCategory': 'Address'},
                    {'name': 'CATEGORY', 'dataType': 'string', 'sourceColumn': 'CATEGORY'},
                    {'name': 'TOTALCOST', 'dataType': 'double', 'sourceColumn': 'TOTALCOST', 'formatString': '$#,0.00;($#,0.00);$#,0.00'}
                ],
                'measures': [
                    {'name': 'Total Spend', 'expression': 'SUM(EVENTS[TOTALCOST])', 'formatString': '$#,0.00;($#,0.00);$#,0.00'},
                    {'name': 'Total Hangouts', 'expression': 'COUNTROWS(EVENTS)'},
                    {'name': 'Avg Hangout Cost', 'expression': 'AVERAGE(EVENTS[TOTALCOST])', 'formatString': '$#,0.00;($#,0.00);$#,0.00'}
                ],
                'partitions': [
                    {
                        'name': 'EVENTS-Partition',
                        'mode': 'import',
                        'source': {
                            'type': 'm',
                            'expression': make_m_expr('EVENTS')
                        }
                    }
                ]
            },
            {
                'name': 'LEDGER',
                'columns': [
                    {'name': 'LEDGERID', 'dataType': 'int64', 'sourceColumn': 'LEDGERID', 'isNullable': False},
                    {'name': 'EVENTID', 'dataType': 'int64', 'sourceColumn': 'EVENTID'},
                    {'name': 'PERSONID', 'dataType': 'int64', 'sourceColumn': 'PERSONID'},
                    {'name': 'AMOUNTPAID', 'dataType': 'double', 'sourceColumn': 'AMOUNTPAID', 'formatString': '$#,0.00;($#,0.00);$#,0.00'},
                    {'name': 'AMOUNTOWED', 'dataType': 'double', 'sourceColumn': 'AMOUNTOWED', 'formatString': '$#,0.00;($#,0.00);$#,0.00'}
                ],
                'measures': [
                    {'name': 'Total Paid', 'expression': 'SUM(LEDGER[AMOUNTPAID])', 'formatString': '$#,0.00;($#,0.00);$#,0.00'},
                    {'name': 'Total Owed', 'expression': 'SUM(LEDGER[AMOUNTOWED])', 'formatString': '$#,0.00;($#,0.00);$#,0.00'},
                    {'name': 'Net Balance', 'expression': '[Total Paid] - [Total Owed]', 'formatString': '$#,0.00;($#,0.00);$#,0.00'},
                    {
                        'name': 'Balance Status',
                        'expression': [
                            'VAR Net = [Net Balance]',
                            'RETURN',
                            'IF (',
                            '    ISBLANK(Net),',
                            '    "-",',
                            '    IF (',
                            '        Net > 0,',
                            '        "Owed $" & FORMAT(Net, "0.00"),',
                            '        IF (',
                            '            Net < 0,',
                            '            "Owes $" & FORMAT(ABS(Net), "0.00"),',
                            '            "Settled"',
                            '        )',
                            '    )',
                            ')'
                        ]
                    },
                    {
                        'name': 'Balance Color Code',
                        'expression': [
                            'VAR Net = [Net Balance]',
                            'RETURN',
                            'IF (',
                            '    Net > 0.01,',
                            '    "#107C41",',
                            '    IF (',
                            '        Net < -0.01,',
                            '        "#D83B01",',
                            '        "#605E5C"',
                            '    )',
                            ')'
                        ]
                    }
                ],
                'partitions': [
                    {
                        'name': 'LEDGER-Partition',
                        'mode': 'import',
                        'source': {
                            'type': 'm',
                            'expression': make_m_expr('LEDGER')
                        }
                    }
                ]
            }
        ],
        'relationships': [
            {
                'name': 'Rel_People_Ledger',
                'fromTable': 'LEDGER',
                'fromColumn': 'PERSONID',
                'toTable': 'PEOPLE',
                'toColumn': 'PERSONID'
            },
            {
                'name': 'Rel_Events_Ledger',
                'fromTable': 'LEDGER',
                'fromColumn': 'EVENTID',
                'toTable': 'EVENTS',
                'toColumn': 'EVENTID'
            }
        ]
    }
}

with open(os.path.join(model_dir, 'model.bim'), 'w', encoding='utf-8') as f:
    json.dump(model_bim, f, indent=2)

print("PBIP template successfully generated at:", pbip_path)

