import os
from openpyxl import load_workbook
from datetime import date
from tkinter import filedialog, Tk
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def select_files(default="",title=""):
    """
    Open a file dialog to select one or more files.
    
    Args:
        title (str): The title of the file dialog window
        
    Returns:
        tuple: Selected file paths
    """
    root = Tk()
    root.withdraw()  # Hide the main window
    files = filedialog.askopenfilenames(initialdir=default,title=title)
    if not files:
        logger.warning(f"No files selected for: {title}")
    return files

def categorize_financial_files(files, file_type_label):
    """
    Categorize financial files into Balance Sheet, Cash Flow, and Income Statement.
    
    Args:
        files (tuple): List of file paths
        file_type_label (str): Label for logging purposes (e.g., "FY" or "LTM")
        
    Returns:
        dict: Dictionary containing categorized file paths
    """
    result = {}
    
    for file_path in files:
        if "Balance" in file_path:
            result["balance"] = file_path
            logger.info(f"Found {file_type_label} Balance Sheet: {os.path.basename(file_path)}")
        elif "Cash" in file_path:
            result["cash_flow"] = file_path
            logger.info(f"Found {file_type_label} Cash Flow Statement: {os.path.basename(file_path)}")
        elif "Income" in file_path:
            result["income"] = file_path
            logger.info(f"Found {file_type_label} Income Statement: {os.path.basename(file_path)}")
    
    return result

# Select DCF template file
logger.info("Starting financial data extraction process")
try:
    DCF_file = select_files(default="C:\AsusWebStorage\ran@benhur.co\MySyncFolder\RaniStuff\IBI\Stock Analysis\Financials",title="Please Select DCF template file")[0]
    logger.info(f"Selected DCF template: {os.path.basename(DCF_file)}")
except IndexError:
    logger.error("No DCF template file selected. Exiting.")
    raise SystemExit("Program terminated: DCF template file is required")

# Select and categorize Fiscal Year (FY) files
Selected_Files_FY = select_files("Please Select Fiscal Year financial files")
fy_files = categorize_financial_files(Selected_Files_FY, "FY")

# Extract individual FY file paths
try:
    Balance_Sheet = fy_files["balance"]
    Cash_Flow_Statement = fy_files["cash_flow"]
    Income_Statement = fy_files["income"]
except KeyError as e:
    logger.error(f"Missing required FY file: {e}")
    raise SystemExit(f"Program terminated: Missing required FY file: {e}")

# Select and categorize Latest Twelve Months (LTM) files
Selected_Files_LTM = select_files("Please Select Latest Twelve Months financial files")
ltm_files = categorize_financial_files(Selected_Files_LTM, "LTM")

# Extract individual LTM file paths
try:
    Balance_Sheet_Q = ltm_files["balance"]
    Cash_Flow_Statement_LTM = ltm_files["cash_flow"]
    Income_Statement_LTM = ltm_files["income"]
except KeyError as e:
    logger.error(f"Missing required LTM file: {e}")
    raise SystemExit(f"Program terminated: Missing required LTM file: {e}")

def load_workbooks():
    """
    Load all required workbooks and their first worksheets.
    
    Returns:
        tuple: Tuple containing target workbook and all source worksheets
    """
    try:
        # Load target DCF file
        logger.info("Loading DCF template file")
        target_file = load_workbook(filename=DCF_file)
        target_sheet = target_file.worksheets[0]  # Select first worksheet
        
        # Load Income Statement files
        logger.info("Loading Income Statement files")
        income_file = load_workbook(filename=Income_Statement)
        income_sheet = income_file.worksheets[0]
        income_file_ltm = load_workbook(filename=Income_Statement_LTM)
        income_sheet_ltm = income_file_ltm.worksheets[0]
        
        # Load Balance Sheet files
        logger.info("Loading Balance Sheet files")
        balance_file = load_workbook(filename=Balance_Sheet)
        balance_sheet = balance_file.worksheets[0]
        balance_file_q = load_workbook(filename=Balance_Sheet_Q)
        balance_sheet_q = balance_file_q.worksheets[0]
        
        # Load Cash Flow Statement files
        logger.info("Loading Cash Flow Statement files")
        cash_flow_file = load_workbook(filename=Cash_Flow_Statement)
        cash_flow_sheet = cash_flow_file.worksheets[0]
        cash_flow_file_ltm = load_workbook(filename=Cash_Flow_Statement_LTM)
        cash_flow_sheet_ltm = cash_flow_file_ltm.worksheets[0]
        
        return (
            target_file, 
            target_sheet, 
            income_sheet, 
            income_sheet_ltm, 
            balance_sheet, 
            balance_sheet_q, 
            cash_flow_sheet, 
            cash_flow_sheet_ltm
        )
    except Exception as e:
        logger.error(f"Error loading workbooks: {e}")
        raise

# Load all workbooks
(
    TargetFile, 
    wb1, 
    Income_wb, 
    Income_wb_LTM, 
    Balance_wb, 
    Balance_wb_Q, 
    Cash_Flow_wb, 
    Cash_Flow_wb_LTM
) = load_workbooks()

# Set basic information in target file
wb1['c1'] = date.today()
Company_Name = Income_wb.cell(2, 3).value  # Get company name from Income Statement
if not Company_Name:
    logger.warning("Company name not found in expected cell, using 'Unknown'")
    Company_Name = "Unknown"
    
wb1['c2'] = Company_Name
logger.info(f"Processing data for company: {Company_Name}")

def extract_financial_data():
    """
    Extract financial data from source files and populate the target DCF file.
    """
    # Define financial metrics to extract
    financial_metrics = {
        "income": [
            {"name": "Period End Date", "target_column": 1, "set_c3": True},
            {"name": "Net Interest Expenses", "target_column": 2},
            {"name": "EBT, Incl. Unusual Items", "target_column": 3},
            {"name": "Income Tax Expense", "target_column": 4},
            {"name": "Net Income to Company", "target_column": 5},
            {"name": "EBIT", "target_column": 6}
        ],
        "balance": [
            {"name": "Total Current Assets", "target_column": 7},
            {"name": "Total Current Liabilities", "target_column": 8}
        ],
        "cashflow": [
            {"name": "Depreciation & Amortization (CF)", "target_column": 11},
            {"name": "Amortization of Deferred Charges (CF)", "target_column": 12},
            {"name": "Cash from Operations", "target_column": 13},
            {"name": "Capital Expenditures", "target_column": 14},
            {"name": "Cash from Financing", "target_column": 15}
        ]
    }
    
    # Create a mapping of all financial data rows
    logger.info("Scanning financial statements for required metrics")
    row_val = []
    for row in range(0, 59):  # Scan first 59 rows
        row_val.append({
            'income_index': row+1,
            'income_value': Income_wb.cell(row+1, 3).value,
            'balance_index': row+1,
            'balance_value': Balance_wb.cell(row+1, 3).value,
            'cashflow_index': row+1,
            'cashflow_value': Cash_Flow_wb.cell(row+1, 3).value
        })
    
    # Process Income Statement metrics
    logger.info("Processing Income Statement metrics")
    for metric in financial_metrics["income"]:
        for i in row_val:
            if i['income_value'] == metric["name"]:
                row_index = i['income_index']
                logger.info(f"Found {metric['name']} at row {row_index}")
                
                # Copy historical data (9 years)
                for j in range(9):
                    wb1.cell(row=15-j, column=metric["target_column"]).value = Income_wb.cell(row_index, column=12-j).value
                
                # Copy LTM data
                wb1.cell(row=16, column=metric["target_column"]).value = Income_wb_LTM.cell(row_index, column=15).value
                
                # Special case for Period End Date
                if metric.get("set_c3", False):
                    wb1['C3'] = wb1.cell(row=16, column=1).value
                break
    
    # Process Balance Sheet metrics
    logger.info("Processing Balance Sheet metrics")
    for metric in financial_metrics["balance"]:
        for i in row_val:
            if i['balance_value'] == metric["name"]:
                row_index = i['balance_index']
                logger.info(f"Found {metric['name']} at row {row_index}")
                
                # Copy historical data (9 years)
                for j in range(9):
                    wb1.cell(row=15-j, column=metric["target_column"]).value = Balance_wb.cell(row_index, column=12-j).value
                
                # Copy LTM data
                wb1.cell(row=16, column=metric["target_column"]).value = Balance_wb_Q.cell(row_index, column=15).value
                break
    
    # Process Cash Flow Statement metrics
    logger.info("Processing Cash Flow Statement metrics")
    for metric in financial_metrics["cashflow"]:
        for i in row_val:
            if i['cashflow_value'] == metric["name"]:
                row_index = i['cashflow_index']
                logger.info(f"Found {metric['name']} at row {row_index}")
                
                # Copy historical data (9 years)
                for j in range(9):
                    wb1.cell(row=15-j, column=metric["target_column"]).value = Cash_Flow_wb.cell(row_index, column=12-j).value
                
                # Copy LTM data
                wb1.cell(row=16, column=metric["target_column"]).value = Cash_Flow_wb_LTM.cell(row_index, column=15).value
                break

# Extract and populate financial data
extract_financial_data()
def save_output_file():
    """
    Save the populated DCF file to a user-selected directory.
    """
    logger.info("Requesting output directory selection")
    path = filedialog.askdirectory(title="Select directory to save the output file")
    
    if not path:
        logger.warning("No directory selected, using current directory")
        path = os.getcwd()
    
    # Create sanitized company name for filename
    safe_company_name = ''.join(c if c.isalnum() else '_' for c in Company_Name)
    file_name = os.path.join(path, f'FCF_Analysis_{safe_company_name}.xlsx')
    
    try:
        TargetFile.save(filename=file_name)
        logger.info(f"File saved successfully: {file_name}")
        print(f'File saved successfully: {file_name}')
        return file_name
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        # Try alternative filename
        alt_file_name = os.path.join(path, 'FCF_Analysis.xlsx')
        try:
            TargetFile.save(filename=alt_file_name)
            logger.info(f"Alternative file saved: {alt_file_name}")
            print(f'Alternative file saved: {alt_file_name}')
            return alt_file_name
        except Exception as e:
            logger.error(f"Error saving alternative file: {e}")
            print(f"Error: Could not save file - {e}")
            return None

# Save the final output file
if __name__ == "__main__":
    output_file = save_output_file()
    if output_file:
        logger.info("Financial data extraction completed successfully")
    else:
        logger.error("Failed to save output file")
