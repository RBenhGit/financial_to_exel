# FCF Data Correlation and Legacy Cleanup - Product Requirements Document

## Project Overview

Improve date correlation tracking in the FCF graphs and remove legacy metadata dependencies while ensuring all dates come directly from financial report data sources.

## Problem Statement

Each point in the FCF graph is a calculation of input parameters from a specific financial report which correlates to a specific report date. Currently:

- FCF graphs may not properly correlate years to actual financial report dates
- The system relies on `dates_metadata.json` which contains artificial metadata
- There's no visibility of the latest report date in the FCF Analysis tab
- Date correlation between Excel mode and API mode is not verified
- Legacy components like `CopyDataNew.py` may no longer be relevant

## Requirements

### Core Functional Requirements

1. **Date Correlation Enhancement**
   - FCF graph years must directly correlate to financial report dates (Period End Date rows in Excel, actual statement dates in API)
   - Latest report date must be displayed next to "Data Source" throughout the application
   - Date correlation must work consistently in both Excel mode and API mode

2. **Legacy Cleanup**
   - Remove dependency on `dates_metadata.json` metadata file
   - Remove all artificial date generation logic
   - Evaluate and potentially remove `CopyDataNew.py` if redundant
   - Clean up any legacy metadata approaches

3. **Date Tracking and Validation**
   - Add validation to ensure FCF calculations correlate to source report dates
   - Implement logging to track date sources throughout analysis pipeline
   - Add warnings when date mismatches are detected

4. **UI/UX Improvements**
   - Display latest report date in FCF Analysis tab
   - Include latest report date in exports and reports
   - Show date source information in analysis outputs
   - Ensure consistency across all analysis types

### Technical Requirements

1. **Excel Mode Enhancement**
   - Use `get_period_dates_from_excel()` function exclusively for date extraction
   - Prioritize actual extracted dates over any fallback metadata
   - Ensure FCF graph years match Period End Date row from Excel files

2. **API Mode Enhancement**
   - Extract and use actual reporting dates from financial statements
   - Use DataFrame indices with actual reporting dates
   - Maintain consistency with Excel mode date handling

3. **Data Processing Updates**
   - Modify `data_processing.py` to remove `dates_metadata.json` dependency
   - Update date extraction logic to use only real financial data
   - Implement robust fallback mechanisms using actual data sources

## Success Criteria

1. **Functional Success**
   - FCF graphs show years that directly correlate to financial report dates
   - Latest report date is visible throughout the application
   - No dependency on artificial metadata files
   - Complete traceability from FCF calculations to source financial reports

2. **Technical Success**
   - All date extraction uses real financial report data
   - Consistent behavior between Excel mode and API mode
   - Clean codebase with legacy components removed
   - Comprehensive test coverage for date correlation

3. **User Experience Success**
   - Clear visibility of data sources and dates
   - Consistent date information across all outputs
   - Reliable date correlation in all analysis modes

## Implementation Phases

### Phase 1: Enhanced Date Tracking
- Update FCF Analysis Streamlit App with latest report date display
- Improve date extraction for API mode
- Enhance Excel mode date handling

### Phase 2: Legacy Cleanup
- Remove `dates_metadata.json` dependency
- Evaluate and clean up `CopyDataNew.py`
- Update all date extraction logic

### Phase 3: Date Correlation Verification
- Add date validation system
- Update reports and exports with date information
- Implement comprehensive logging

### Phase 4: Testing and Validation
- Create comprehensive date correlation tests
- Verify both Excel and API modes
- Update documentation

## Acceptance Criteria

1. FCF graph years must match the actual dates from financial reports
2. Latest report date must be displayed next to Data Source in FCF Analysis tab
3. All exports and reports must include latest report date
4. No references to `dates_metadata.json` in codebase
5. Date correlation must work identically in Excel and API modes
6. All date extraction must use real financial data, not artificial metadata
7. System must provide clear warnings for any date inconsistencies
8. Legacy cleanup must not break any existing functionality

## Dependencies

- Excel utility functions for date extraction
- Financial data processing pipeline
- Streamlit UI components
- Report generation system
- Export functionality

## Risks and Mitigation

1. **Risk**: Breaking existing functionality during legacy cleanup
   - **Mitigation**: Comprehensive testing before removing any components

2. **Risk**: Date extraction failures in edge cases
   - **Mitigation**: Robust fallback mechanisms using actual financial data

3. **Risk**: Inconsistency between Excel and API modes
   - **Mitigation**: Unified date handling approach with validation

## Timeline

Estimated completion: 4-6 weeks

- Phase 1: 1-2 weeks
- Phase 2: 1-2 weeks  
- Phase 3: 1 week
- Phase 4: 1 week

## Technical Notes

- Prioritize `excel_utils.py:get_period_dates_from_excel()` for Excel date extraction
- Use DataFrame indices for API mode date handling
- Ensure `data_processing.py:prepare_fcf_data()` uses only real dates
- Remove `CopyDataNew.py:435-450` metadata creation logic
- Update `fcf_analysis_streamlit.py` to display latest report dates