import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# CONFIGURATION
# ============================================================
GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
WORKSHEET_NAME = "Sheet1"
GOOGLE_CREDENTIALS_FILE = "quixotic-prism-502006-u3-86172ccb7319.json"

JOTFORM_API_KEY = os.environ["JOTFORM_API_KEY"]
FORM_ID = "251590768630059"

PAGE_SIZE = 100

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    GOOGLE_CREDENTIALS_FILE,
    scopes=SCOPES
)

client = gspread.authorize(creds)

sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet(WORKSHEET_NAME)

# ============================================================
# HELPER FUNCTION
# ============================================================

def get_answer(answers, question):
    """
    Returns the answer for a given Jotform question.
    """

    for answer in answers.values():

        if answer.get("text") == question:

            value = answer.get("answer", "")

            if isinstance(value, list):
                return ", ".join(map(str, value))

            return str(value)

    return ""


# ============================================================
# FETCH ALL SUBMISSIONS (PAGINATION)
# ============================================================

print("Fetching submissions from Jotform...\n")

offset = 0
submissions = []

while True:

    url = (
        f"https://api.jotform.com/form/{FORM_ID}/submissions"
        f"?apiKey={JOTFORM_API_KEY}"
        f"&limit={PAGE_SIZE}"
        f"&offset={offset}"
    )

    response = requests.get(url)

    if response.status_code != 200:
        print("Error:", response.text)
        exit()

    page = response.json().get("content", [])

    if not page:
        break

    submissions.extend(page)

    print(f"Fetched {len(page)} submissions (Total: {len(submissions)})")

    if len(page) < PAGE_SIZE:
        break

    offset += PAGE_SIZE

print("\n==============================================")
print(f"Total Submissions Fetched : {len(submissions)}")
print("==============================================")

# ============================================================
# FILTER ONLY VM DECOMMISSION
# ============================================================

filtered_submissions = []

for submission in submissions:

    answers = submission.get("answers", {})

    operation = get_answer(answers, "Select Operation").strip()

    if operation.lower() == "vm decommission":
        filtered_submissions.append(submission)

print(f"VM Decommission Records : {len(filtered_submissions)}")

# ============================================================
# CREATE RECORDS
# ============================================================

records = []

for submission in filtered_submissions:

    answers = submission["answers"]

    record = {

        "Lead ID": get_answer(answers, "Lead ID"),

        "Submission Date": submission.get("created_at", ""),

        "Select Operation": get_answer(answers, "Select Operation"),

        "Select Current Stage Of Operation":
            get_answer(answers, "Select Current Stage Of Operation"),

        "Pending Task":
            get_answer(answers, "Pending Task"),

        "Task Pending On":
            get_answer(answers, "Task Pending On"),

        "Flow Status":
            get_answer(answers, "Flow Status"),

        "Decommission SPOC Name":
            get_answer(answers, "Decommission SPOC Name"),

        "Decommission SPOC Email":
            get_answer(answers, "Decommission SPOC Email"),

        "Decommission Form Is Filled By":
            get_answer(answers, "Decommission Form Is Filled By"),

        "Client Name":
            get_answer(answers, "Client Name"),

        "Reason For Decommission":
            get_answer(answers, "Reason For Decommission"),

        "Status of EST Assessment on Decommission":
            get_answer(
                answers,
                "Status of EST Assessment on Decommission"
            ),

        "Form Submission Date":
            get_answer(answers, "Form Submission Date"),

        "Client Email":
            get_answer(answers, "Client Email"),

        "Number Of Machines for Decommission":
            get_answer(
                answers,
                "Number Of Machines for Decommission"
            ),

        "Enter VMIDs for decommission":
            get_answer(
                answers,
                "Enter VMIDs for decommission"
            ),

        "Select Current Stage For Decommission":
            get_answer(
                answers,
                "Select Current Stage For Decommission"
            ),

        "Submission ID":
            submission.get("id", "")

    }

    records.append(record)

# ============================================================
# GOOGLE SHEETS SYNC (APPEND NEW RECORDS ONLY)
# ============================================================

print("\nSyncing Google Sheet...")

if len(records) == 0:
    print("No VM Decommission records found.")
    exit()

headers = list(records[0].keys())

# Read existing sheet
sheet_data = sheet.get_all_values()

# ============================================================
# CREATE HEADER IF MISSING
# ============================================================

headers = list(records[0].keys())

sheet_data = sheet.get_all_values()

# New sheet or empty first row
if len(sheet_data) == 0 or sheet_data[0] == []:

    print("Creating headers...")

    sheet.update(
        "A1",
        [headers]
    )

    sheet_data = [headers]

# Header missing or different
elif sheet_data[0] != headers:

    print("Updating headers...")

    sheet.update(
        "A1",
        [headers]
    )

    sheet_data[0] = headers

# ------------------------------------------------------------
# Existing Submission IDs
# ------------------------------------------------------------

submission_col = headers.index("Submission ID")

existing_submission_ids = set()

if len(sheet_data) > 1:

    for row in sheet_data[1:]:

        if len(row) > submission_col:

            existing_submission_ids.add(row[submission_col])

print(f"Existing records in Google Sheet : {len(existing_submission_ids)}")

# ------------------------------------------------------------
# Prepare new rows
# ------------------------------------------------------------

rows_to_insert = []

for record in records:

    submission_id = str(record["Submission ID"])

    # Skip already synced records
    if submission_id in existing_submission_ids:
        continue

    row = [str(record.get(col, "")) for col in headers]

    rows_to_insert.append(row)

# ------------------------------------------------------------
# Bulk Insert
# ------------------------------------------------------------

if rows_to_insert:

    sheet.append_rows(rows_to_insert)

print("\n======================================")
print("SYNC COMPLETED")
print("======================================")
print(f"New Rows Inserted : {len(rows_to_insert)}")
print(f"Skipped Existing  : {len(records)-len(rows_to_insert)}")
print("======================================")

'''    
# ============================================================
# DISPLAY RESULTS
# ============================================================

if len(records) == 0:
    print("\nNo VM Decommission records found.")
    exit()

print("\n")
print("=" * 130)
print("VM DECOMMISSION RECORDS")
print("=" * 130)

for i, record in enumerate(records, start=1):

    print(f"\n{'='*130}")
    print(f"RECORD {i}")
    print(f"{'='*130}")

    for key, value in record.items():
        print(f"{key:<45}: {value}")

print("\nCompleted Successfully.")
'''
