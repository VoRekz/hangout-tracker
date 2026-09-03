import json
import uuid
import os

report_json_path = os.path.join('Hangout_Dashboard.Report', 'report.json')

with open(report_json_path, 'r', encoding='utf-8') as f:
    report_data = json.load(f)

def make_card(title, measure_table, measure_name, x, y, width, height):
    vid = uuid.uuid4().hex[:16]
    query_ref = f"{measure_table}.{measure_name}"
    config = {
        "name": vid,
        "layouts": [{
            "id": 0,
            "position": {"x": x, "y": y, "z": 0, "width": width, "height": height}
        }],
        "singleVisual": {
            "visualType": "card",
            "projections": {
                "Values": [{"queryRef": query_ref}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "t", "Entity": measure_table, "Type": 0}],
                "Select": [{
                    "Measure": {
                        "Expression": {"SourceRef": {"Source": "t"}},
                        "Property": measure_name
                    },
                    "Name": query_ref,
                    "NativeReferenceName": measure_name
                }]
            }
        }
    }
    return {
        "x": float(x), "y": float(y), "z": 0.0, "width": float(width), "height": float(height),
        "config": json.dumps(config)
    }

def make_table(x, y, width, height):
    vid = uuid.uuid4().hex[:16]
    config = {
        "name": vid,
        "layouts": [{
            "id": 0,
            "position": {"x": x, "y": y, "z": 1, "width": width, "height": height}
        }],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {
                "Values": [
                    {"queryRef": "PEOPLE.NAME"},
                    {"queryRef": "LEDGER.Total Paid"},
                    {"queryRef": "LEDGER.Total Owed"},
                    {"queryRef": "LEDGER.Net Balance"},
                    {"queryRef": "LEDGER.Balance Status"}
                ]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [
                    {"Name": "p", "Entity": "PEOPLE", "Type": 0},
                    {"Name": "l", "Entity": "LEDGER", "Type": 0}
                ],
                "Select": [
                    {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "p"}},
                            "Property": "NAME"
                        },
                        "Name": "PEOPLE.NAME",
                        "NativeReferenceName": "Friend"
                    },
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "l"}},
                            "Property": "Total Paid"
                        },
                        "Name": "LEDGER.Total Paid",
                        "NativeReferenceName": "Total Paid"
                    },
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "l"}},
                            "Property": "Total Owed"
                        },
                        "Name": "LEDGER.Total Owed",
                        "NativeReferenceName": "Total Owed"
                    },
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "l"}},
                            "Property": "Net Balance"
                        },
                        "Name": "LEDGER.Net Balance",
                        "NativeReferenceName": "Net Balance"
                    },
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "l"}},
                            "Property": "Balance Status"
                        },
                        "Name": "LEDGER.Balance Status",
                        "NativeReferenceName": "Status"
                    }
                ]
            }
        }
    }
    return {
        "x": float(x), "y": float(y), "z": 1.0, "width": float(width), "height": float(height),
        "config": json.dumps(config)
    }

def make_map(x, y, width, height):
    vid = uuid.uuid4().hex[:16]
    config = {
        "name": vid,
        "layouts": [{
            "id": 0,
            "position": {"x": x, "y": y, "z": 2, "width": width, "height": height}
        }],
        "singleVisual": {
            "visualType": "map",
            "projections": {
                "Location": [{"queryRef": "EVENTS.ADDRESS"}],
                "Size": [{"queryRef": "EVENTS.Total Spend"}],
                "Series": [{"queryRef": "EVENTS.CATEGORY"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "e", "Entity": "EVENTS", "Type": 0}],
                "Select": [
                    {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "e"}},
                            "Property": "ADDRESS"
                        },
                        "Name": "EVENTS.ADDRESS",
                        "NativeReferenceName": "Location"
                    },
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "e"}},
                            "Property": "Total Spend"
                        },
                        "Name": "EVENTS.Total Spend",
                        "NativeReferenceName": "Total Cost"
                    },
                    {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "e"}},
                            "Property": "CATEGORY"
                        },
                        "Name": "EVENTS.CATEGORY",
                        "NativeReferenceName": "Category"
                    }
                ]
            }
        }
    }
    return {
        "x": float(x), "y": float(y), "z": 2.0, "width": float(width), "height": float(height),
        "config": json.dumps(config)
    }

def make_donut(x, y, width, height):
    vid = uuid.uuid4().hex[:16]
    config = {
        "name": vid,
        "layouts": [{
            "id": 0,
            "position": {"x": x, "y": y, "z": 3, "width": width, "height": height}
        }],
        "singleVisual": {
            "visualType": "donutChart",
            "projections": {
                "Category": [{"queryRef": "EVENTS.CATEGORY"}],
                "Y": [{"queryRef": "EVENTS.Total Spend"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "e", "Entity": "EVENTS", "Type": 0}],
                "Select": [
                    {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "e"}},
                            "Property": "CATEGORY"
                        },
                        "Name": "EVENTS.CATEGORY",
                        "NativeReferenceName": "Category"
                    },
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "e"}},
                            "Property": "Total Spend"
                        },
                        "Name": "EVENTS.Total Spend",
                        "NativeReferenceName": "Total Spend"
                    }
                ]
            }
        }
    }
    return {
        "x": float(x), "y": float(y), "z": 3.0, "width": float(width), "height": float(height),
        "config": json.dumps(config)
    }

# Build visual list
visuals = [
    # Top 3 KPI Cards
    make_card("Total Spend", "EVENTS", "Total Spend", 20, 20, 260, 110),
    make_card("Total Hangouts", "EVENTS", "Total Hangouts", 300, 20, 260, 110),
    make_card("Avg Hangout Cost", "EVENTS", "Avg Hangout Cost", 580, 20, 260, 110),
    
    # Left: Friend Balance Sheet Table
    make_table(20, 150, 560, 540),
    
    # Right Top: Location Map Heatmap
    make_map(600, 150, 650, 280),
    
    # Right Bottom: Category Spend Breakdown Donut
    make_donut(600, 450, 650, 240)
]

report_data["sections"][0]["visualContainers"] = visuals

with open(report_json_path, "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2)

print(f"Successfully generated {len(visuals)} visuals in report.json!")

