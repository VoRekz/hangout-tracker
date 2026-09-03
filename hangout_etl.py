import platform
# Fix for Windows Store Python execution alias with snowflake-connector
platform.libc_ver = lambda *args, **kwargs: ('', '')

import os
import re
import urllib.parse
import pandas as pd
from sqlalchemy import create_engine

# 1. Load local .env if present (ignored by git)
def load_env():
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip()
load_env()

# Connect to Snowflake (Supports GitHub Secrets / Environment Variables)
USER = os.environ.get("SNOWFLAKE_USER", "VOREKZ")
RAW_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD", "")
PASSWORD = urllib.parse.quote_plus(RAW_PASSWORD)
ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT", "kdicljj-hs69473")
DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "HangoutTracker")
SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA", "Core")
WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
ROLE = os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN")

ENGINE_URL = f"snowflake://{USER}:{PASSWORD}@{ACCOUNT}/{DATABASE}/{SCHEMA}?warehouse={WAREHOUSE}&role={ROLE}"
engine = create_engine(ENGINE_URL)

# Map names exactly as they appear in your Google Form / Spreadsheet
PEOPLE_MAP = {
    'Julio': 1, 'Girlfriend': 2, 'Barbara': 3,
    'Karla': 4, 'Holden': 5, 'Josue': 6
}

DEFAULT_GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1h_Smwy2so7-1IRHIJR8MbXTOUyHSO5y_jOWq6eWuSrM/edit"

def load_data(source=None):
    """
    Loads data from:
    1. Google Sheets URL (via environment variable GOOGLE_SHEET_URL or argument)
    2. Local Excel file ('hangout_responses.xlsx')
    3. Local CSV file ('hangout_responses.csv')
    """
    url = source or os.environ.get("GOOGLE_SHEET_URL", DEFAULT_GOOGLE_SHEET_URL)
    
    if url and ("docs.google.com/spreadsheets" in url or url.startswith("http")):
        # Extract Sheet ID and convert to direct CSV export URL
        sheet_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
        if sheet_id_match:
            sheet_id = sheet_id_match.group(1)
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        else:
            csv_url = url
            
        print(f"Loading live responses from Google Sheets: {csv_url}")
        return pd.read_csv(csv_url)
    
    # Fallback to local files
    if source and os.path.exists(source):
        target = source
    elif os.path.exists('hangout_responses.xlsx'):
        target = 'hangout_responses.xlsx'
    elif os.path.exists('hangout_responses.csv'):
        target = 'hangout_responses.csv'
    else:
        raise FileNotFoundError("Could not find Google Sheet URL or local response spreadsheet.")
    
    print(f"Loading data from local file: {target}")
    if target.endswith('.xlsx') or target.endswith('.xls'):
        return pd.read_excel(target)
    return pd.read_csv(target)

def process_and_upload(source=None):
    df = load_data(source)
    
    # Normalize column names in case Google Forms adds extra whitespace or timestamps
    col_mapping = {c: c.strip() for c in df.columns}
    df.rename(columns=col_mapping, inplace=True)
    
    # 2. Get current Max IDs, existing people, and events from Snowflake for Deduplication
    try:
        current_event_id = pd.read_sql("SELECT COALESCE(MAX(EventID), 100) FROM Events", engine).iloc[0, 0]
        current_ledger_id = pd.read_sql("SELECT COALESCE(MAX(LedgerID), 1000) FROM Ledger", engine).iloc[0, 0]
        
        # Load existing people live from Snowflake
        people_df = pd.read_sql("SELECT PersonID, Name FROM People", engine)
        people_map = {str(r['name']).strip().lower(): int(r['personid']) for _, r in people_df.iterrows()}
        max_person_id = int(people_df['personid'].max()) if not people_df.empty else 0
        new_people_to_insert = []
        
        # Helper to get existing ID or auto-register a new friend
        def get_or_register_person(raw_name):
            nonlocal max_person_id
            name = str(raw_name).strip()
            if not name:
                return None
            key = name.lower()
            if key in people_map:
                return people_map[key]
            
            # Auto-register new friend
            max_person_id += 1
            new_id = max_person_id
            display_name = name.title()
            people_map[key] = new_id
            new_people_to_insert.append({'personid': new_id, 'name': display_name})
            print(f"🎉 Auto-registered new friend to Snowflake: '{display_name}' (ID: {new_id})")
            return new_id
        
        # Pull existing events to prevent duplicates
        existing_df = pd.read_sql("SELECT EventDate, Location, TotalCost FROM Events", engine)
        existing_keys = {
            (
                pd.to_datetime(r['eventdate']).strftime('%Y-%m-%d'),
                str(r['location']).strip().lower(),
                round(float(r['totalcost']), 2)
            )
            for _, r in existing_df.iterrows()
        }
    except Exception as e:
        print("Failed to query Snowflake. Check connection credentials and schema:\n", e)
        return

    events_data = []
    ledger_data = []

    for index, row in df.iterrows():
        # Clean and standardize date & location
        try:
            event_date = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
        except Exception:
            print(f"Skipping invalid date row {index}: {row.get('Date')}")
            continue
            
        location = str(row.get('Location', '')).strip()
        try:
            total_cost = round(float(row.get('TotalCost', 0.0)), 2)
        except (ValueError, TypeError):
            print(f"Skipping invalid cost row {index}: {row.get('TotalCost')}")
            continue
            
        # Deduplication check
        row_key = (event_date, location.lower(), total_cost)
        if row_key in existing_keys:
            # Already in Snowflake
            continue
            
        current_event_id += 1
        existing_keys.add(row_key) # Track newly added in this run
        
        # Build Events Payload (supports multiple suggesters or custom categories)
        events_data.append({
            'EventID': current_event_id,
            'EventDate': event_date,
            'Location': location,
            'Address': str(row.get('Address', 'Dallas TX')).strip(),
            'Category': str(row.get('Category', 'Other')).strip(),
            'TotalCost': total_cost,
            'SuggestedBy': str(row.get('SuggestedBy', 'Unknown')).strip()
        })
        
        # Calculate Splits
        attendees = [name.strip() for name in str(row.get('Attendees', '')).split(',') if name.strip()]
        if not attendees:
            print(f"Skipping event {event_date} - {location}: No valid attendees listed.")
            continue
            
        split_cost = round(total_cost / len(attendees), 2)
        payer = str(row.get('PaidBy', '')).strip()
        
        # Build Ledger Payload (dynamically registers new attendees / payers if unknown)
        for person in attendees:
            person_id = get_or_register_person(person)
            if not person_id:
                continue
                
            current_ledger_id += 1
            amount_paid = total_cost if person.lower() == payer.lower() else 0.00
            
            ledger_data.append({
                'LedgerID': current_ledger_id,
                'EventID': current_event_id,
                'PersonID': person_id,
                'AmountPaid': amount_paid,
                'AmountOwed': split_cost
            })
            
    # 3. Push only new records to Snowflake
    if not events_data:
        print("Snowflake is already up to date! 0 new hangouts to upload.")
        return

    events_df = pd.DataFrame(events_data)
    ledger_df = pd.DataFrame(ledger_data)
    
    # Lowercase column names so Snowflake connector does not double-quote them
    events_df.columns = [c.lower() for c in events_df.columns]
    ledger_df.columns = [c.lower() for c in ledger_df.columns]
    
    with engine.connect() as conn:
        if new_people_to_insert:
            people_insert_df = pd.DataFrame(new_people_to_insert)
            people_insert_df.columns = [c.lower() for c in people_insert_df.columns]
            people_insert_df.to_sql(name='people', con=conn, if_exists='append', index=False, method='multi')
            print(f"Added {len(people_insert_df)} new friend(s) to Snowflake People table.")
            
        events_df.to_sql(name='events', con=conn, if_exists='append', index=False, method='multi')
        ledger_df.to_sql(name='ledger', con=conn, if_exists='append', index=False, method='multi')
        
    print(f"Success! Uploaded {len(events_df)} new event(s) and {len(ledger_df)} new ledger entry(ies) to Snowflake.")

if __name__ == "__main__":
    process_and_upload()
