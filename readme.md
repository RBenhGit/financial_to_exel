# CopyDataNew.py

## Overview
CopyDataNew.py is a Python script designed to manage and transfer 10yr financial reports. This script reads Execel files exported from Investing.com.
It performs necessary transformations or validations, and copies the data to a predefined DCF template where a discounted cashflow analysis is performed.

## Work Flow
1. Create parent folder mkdir <Tiker name> (GOOG)
2. Create sub folders FY (Fiscal Year) and LTM (Latest Twelve Mounth) using the mkdir command
3. Export from investing.com the 10yr income statement, Balance Sheet, Cashflow Statement into the <FY> folder.
4. Export from investing.com the 3yr income statement, Cashflow Statement into the <LTM> folder.
5. Export from investing.com the 3yr Balance Sheet into the <LTM> folder.
6. if needed instal the requirements using the command: install -r requirements.txt
7. run the programe with the command: python CopyDataNew.py 
8. Step I: a search window will be opened asking for the template DCF file. Locate the file and continue.
9. Step II: a search window will be opened asking for the FY folder. Select it and continue.
10. Step III: a search window will be opened asking for the LTM folder. Select it and continue.
11 Step IV: a search window will be opened asking for the folder where the output DCF file will be saved. 
   It is recomanded to save it in the parent Tiker folder.

## DCF Calculation using the Output execell file.
12. open the excell output DCF file.
13. In the "Data Entry" tab go to the "Ticker" value and convert to stock in the "Data" menu.
14. Go to "DCF" tab and adjust the Growth rates and Required rate of return as needed. One can use the 3yr, 5yr and 10yr average growth values as aid.  
    Also, a visual graphs to aid decision is located at "Free Cash Flow Graph" and "Growth YoY Graph".

## Included files and folders
15. DCF calculation template file: FCF_Analysis_temp1.xlsx
16. An Example folder GOOG with sub folders.