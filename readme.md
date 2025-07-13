# CopyDataNew.py

## Overview
CopyDataNew.py is a Python script designed to manage and transfer 10yr financial reports. This script reads Excel files exported from Investing.com.
It performs necessary transformations or validations, and copies the data to a predefined DCF template where a discounted cashflow analysis is performed.

## Work Flow
1. Create parent folder mkdir <Tiker name> (GOOG)
2. Create sub folders FY (Fiscal Year) and LTM (Latest Twelve Mounth) using the mkdir command
3. Export from investing.com the 10yr income statement, Balance Sheet, Cashflow Statement into the <FY> folder.
4. Export from investing.com the 3yr latest twelve mount income statement, Cashflow Statement into the <LTM> folder.
5. Export from investing.com the 3yr quaterly Balance Sheet into the <LTM> folder.
6. if needed instal the requirements using the command: install -r requirements.txt
7. run the programe with the command: python CopyDataNew.py 
8. Step I: a search window will be opened asking for the template DCF file. Locate the file and continue.
9. Step II: a search window will be opened asking for the FY folder. Select it and continue.
10. Step III: a search window will be opened asking for the LTM folder. Select it and continue.
11 Step IV: a search window will be opened asking for the folder where the output DCF file will be saved. 
   It is recomanded to save it in the parent Tiker folder.

## DCF Calculation using the Output Excel file.
12. open the excel output DCF file.
13. In the "Data Entry" tab go to the "Ticker" value and convert to stock in the "Data" menu.
14. Go to "DCF" tab and adjust the Growth rates and Required rate of return as needed. One can use the 3yr, 5yr and 10yr average growth values as aid.  
    Also, a visual graphs to aid decision is located at "Free Cash Flow Graph" and "Growth YoY Graph".

## DCF Fair Value Calculation Methodology

### Overview
The DCF (Discounted Cash Flow) analysis in this application uses a comprehensive 10-year projection model with terminal value calculation to determine the fair value per share of a company.

### Calculation Process

#### **1. Base FCF Determination**
- Uses the most recent Free Cash Flow to Firm (FCFF) value from historical data
- Falls back to $100M if no historical data is available

#### **2. Growth Rate Assumptions**
- **Years 1-5**: Uses 3-year historical growth rate (or user input)
- **Years 5-10**: Uses 5-year historical growth rate (or user input)  
- **Terminal Growth**: Default 3% perpetual growth rate (user adjustable)

#### **3. 10-Year FCF Projections**
Each year's FCF is calculated as:
```
FCF(year) = Previous FCF × (1 + Growth Rate)
```

#### **4. Terminal Value Calculation (Gordon Growth Model)**
```
Terminal Value = FCF₁₁ / (Discount Rate - Terminal Growth Rate)
```
Where FCF₁₁ = Final projected FCF × (1 + Terminal Growth Rate)

#### **5. Present Value Calculations**
- **PV of each FCF**: `FCF(t) / (1 + Discount Rate)^t`
- **PV of Terminal Value**: `Terminal Value / (1 + Discount Rate)^10`

#### **6. Enterprise Value**
```
Enterprise Value = Sum of all PV of FCF + PV of Terminal Value
```

#### **7. Equity Value**
```
Equity Value = Enterprise Value - Net Debt
```
*Note: Net debt is estimated from financing cash flows or set to 0 if unavailable*

#### **8. Fair Value Per Share**
```
Fair Value Per Share = Equity Value × 1,000,000 / Shares Outstanding
```

### Key Components

**Shares Outstanding**: Determined via Yahoo Finance API using:
```
Shares Outstanding = Market Cap / Current Stock Price
```

**Discount Rate**: Default 12% (user adjustable)

**Terminal Growth Rate**: Default 3% (user adjustable)

### Complete DCF Formula
```
Fair Value = [Σ(FCF(t)/(1+r)^t) + (TV/(1+r)^10) - Net Debt] × 1M / Shares Outstanding
```

Where:
- FCF(t) = Free Cash Flow in year t
- r = Discount rate (Required Rate of Return)
- TV = Terminal Value
- Net Debt = Estimated net debt position

### Sensitivity Analysis
The system includes sensitivity analysis that recalculates the fair value across different discount rates and growth rate assumptions to show how sensitive the valuation is to key assumptions.

## Included files and folders
15. DCF calculation template file: FCF_Analysis_temp1.xlsx
16. An Example folder GOOG with sub folders.