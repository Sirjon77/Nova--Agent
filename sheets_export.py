import gspread
from oauth2client.service_account import ServiceAccountCredentials

def export_to_google_sheet(sheet_name, data_list):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    for row in data_list:
        sheet.append_row(row)