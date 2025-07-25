"""
Watch List Manager Module

This module handles watch list creation, storage, and management for tracking
DCF analysis results across multiple companies and time periods.
"""

import json
import sqlite3
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
from config import get_export_directory, get_export_config, ensure_export_directory

logger = logging.getLogger(__name__)

class WatchListManager:
    """
    Manages watch lists with analysis tracking capabilities
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize watch list manager
        
        Args:
            data_dir (str): Directory to store watch list data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.json_file = self.data_dir / "watch_lists.json"
        self.db_file = self.data_dir / "watch_lists.db"
        
        # Initialize storage
        self._init_json_storage()
        self._init_sqlite_storage()
    
    def _init_json_storage(self):
        """Initialize JSON storage file if it doesn't exist"""
        if not self.json_file.exists():
            initial_data = {
                "watch_lists": {},
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            with open(self.json_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def _init_sqlite_storage(self):
        """Initialize SQLite database for watch lists"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create watch_lists table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS watch_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_date TEXT NOT NULL,
            updated_date TEXT NOT NULL
        )
        ''')
        
        # Create analysis_records table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            watch_list_id INTEGER,
            ticker TEXT NOT NULL,
            company_name TEXT,
            analysis_date TEXT NOT NULL,
            current_price REAL,
            fair_value REAL,
            discount_rate REAL,
            terminal_growth_rate REAL,
            upside_downside_pct REAL,
            fcf_type TEXT,
            dcf_assumptions TEXT,
            analysis_metadata TEXT,
            FOREIGN KEY (watch_list_id) REFERENCES watch_lists (id)
        )
        ''')
        
        # Create index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON analysis_records (ticker)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_records (analysis_date)')
        
        conn.commit()
        conn.close()
    
    def create_watch_list(self, name: str, description: str = "") -> bool:
        """
        Create a new watch list
        
        Args:
            name (str): Watch list name
            description (str): Optional description
            
        Returns:
            bool: True if created successfully, False if name already exists
        """
        try:
            # Check if name already exists
            if self.get_watch_list(name):
                logger.warning(f"Watch list '{name}' already exists")
                return False
            
            # Add to SQLite
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            cursor.execute('''
            INSERT INTO watch_lists (name, description, created_date, updated_date)
            VALUES (?, ?, ?, ?)
            ''', (name, description, current_time, current_time))
            
            conn.commit()
            conn.close()
            
            # Add to JSON as backup
            with open(self.json_file, 'r') as f:
                data = json.load(f)
            
            data["watch_lists"][name] = {
                "description": description,
                "created_date": current_time,
                "updated_date": current_time,
                "stocks": []
            }
            
            with open(self.json_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Created watch list: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating watch list '{name}': {e}")
            return False
    
    def get_watch_list(self, name: str, latest_only: bool = True) -> Optional[Dict]:
        """
        Get watch list by name
        
        Args:
            name (str): Watch list name
            latest_only (bool): If True, returns only latest analysis per ticker
            
        Returns:
            dict: Watch list data or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM watch_lists WHERE name = ?', (name,))
            result = cursor.fetchone()
            
            if result:
                watch_list_id, name, description, created_date, updated_date = result
                
                if latest_only:
                    # Get only the latest analysis for each ticker
                    cursor.execute('''
                    SELECT ar.ticker, ar.company_name, ar.analysis_date, ar.current_price, ar.fair_value,
                           ar.discount_rate, ar.terminal_growth_rate, ar.upside_downside_pct, ar.fcf_type,
                           ar.dcf_assumptions, ar.analysis_metadata
                    FROM analysis_records ar
                    INNER JOIN (
                        SELECT ticker, MAX(analysis_date) as latest_date
                        FROM analysis_records 
                        WHERE watch_list_id = ?
                        GROUP BY ticker
                    ) latest ON ar.ticker = latest.ticker AND ar.analysis_date = latest.latest_date
                    WHERE ar.watch_list_id = ?
                    ORDER BY ar.analysis_date DESC
                    ''', (watch_list_id, watch_list_id))
                else:
                    # Get all analysis records
                    cursor.execute('''
                    SELECT ticker, company_name, analysis_date, current_price, fair_value,
                           discount_rate, terminal_growth_rate, upside_downside_pct, fcf_type,
                           dcf_assumptions, analysis_metadata
                    FROM analysis_records 
                    WHERE watch_list_id = ?
                    ORDER BY analysis_date DESC
                    ''', (watch_list_id,))
                
                records = cursor.fetchall()
                stocks = []
                
                for record in records:
                    stock_data = {
                        "ticker": record[0],
                        "company_name": record[1],
                        "analysis_date": record[2],
                        "current_price": record[3],
                        "fair_value": record[4],
                        "discount_rate": record[5],
                        "terminal_growth_rate": record[6],
                        "upside_downside_pct": record[7],
                        "fcf_type": record[8],
                        "dcf_assumptions": json.loads(record[9]) if record[9] else {},
                        "analysis_metadata": json.loads(record[10]) if record[10] else {}
                    }
                    stocks.append(stock_data)
                
                conn.close()
                
                return {
                    "name": name,
                    "description": description,
                    "created_date": created_date,
                    "updated_date": updated_date,
                    "stocks": stocks,
                    "latest_only": latest_only
                }
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Error getting watch list '{name}': {e}")
            return None
    
    def list_watch_lists(self) -> List[Dict]:
        """
        Get all watch lists
        
        Returns:
            list: List of watch list summaries
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT wl.name, wl.description, wl.created_date, wl.updated_date,
                   COUNT(ar.id) as stock_count
            FROM watch_lists wl
            LEFT JOIN analysis_records ar ON wl.id = ar.watch_list_id
            GROUP BY wl.id, wl.name, wl.description, wl.created_date, wl.updated_date
            ORDER BY wl.updated_date DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            watch_lists = []
            for result in results:
                watch_lists.append({
                    "name": result[0],
                    "description": result[1],
                    "created_date": result[2],
                    "updated_date": result[3],
                    "stock_count": result[4]
                })
            
            return watch_lists
            
        except Exception as e:
            logger.error(f"Error listing watch lists: {e}")
            return []
    
    def add_analysis_to_watch_list(self, watch_list_name: str, analysis_data: Dict) -> bool:
        """
        Add analysis result to a watch list
        
        Args:
            watch_list_name (str): Watch list name
            analysis_data (dict): Analysis data containing DCF results
            
        Returns:
            bool: True if added successfully
        """
        try:
            # Get watch list ID
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM watch_lists WHERE name = ?', (watch_list_name,))
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"Watch list '{watch_list_name}' not found")
                conn.close()
                return False
            
            watch_list_id = result[0]
            
            # Prepare analysis data
            ticker = analysis_data.get('ticker', 'UNKNOWN')
            company_name = analysis_data.get('company_name', '')
            analysis_date = datetime.now().isoformat()
            current_price = analysis_data.get('current_price', 0.0)
            fair_value = analysis_data.get('fair_value', 0.0)
            discount_rate = analysis_data.get('discount_rate', 0.0)
            terminal_growth_rate = analysis_data.get('terminal_growth_rate', 0.0)
            
            # Calculate upside/downside percentage
            if current_price and fair_value:
                upside_downside_pct = ((fair_value - current_price) / current_price) * 100
            else:
                upside_downside_pct = 0.0
            
            fcf_type = analysis_data.get('fcf_type', 'FCFE')
            dcf_assumptions = json.dumps(analysis_data.get('dcf_assumptions', {}))
            analysis_metadata = json.dumps(analysis_data.get('metadata', {}))
            
            # Insert analysis record
            cursor.execute('''
            INSERT INTO analysis_records 
            (watch_list_id, ticker, company_name, analysis_date, current_price, 
             fair_value, discount_rate, terminal_growth_rate, upside_downside_pct, 
             fcf_type, dcf_assumptions, analysis_metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (watch_list_id, ticker, company_name, analysis_date, current_price,
                  fair_value, discount_rate, terminal_growth_rate, upside_downside_pct,
                  fcf_type, dcf_assumptions, analysis_metadata))
            
            # Update watch list updated_date
            cursor.execute('''
            UPDATE watch_lists SET updated_date = ? WHERE id = ?
            ''', (analysis_date, watch_list_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added analysis for {ticker} to watch list '{watch_list_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error adding analysis to watch list '{watch_list_name}': {e}")
            return False
    
    def remove_stock_from_watch_list(self, watch_list_name: str, ticker: str) -> bool:
        """
        Remove all analysis records for a ticker from a watch list
        
        Args:
            watch_list_name (str): Watch list name
            ticker (str): Stock ticker to remove
            
        Returns:
            bool: True if removed successfully
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get watch list ID
            cursor.execute('SELECT id FROM watch_lists WHERE name = ?', (watch_list_name,))
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"Watch list '{watch_list_name}' not found")
                conn.close()
                return False
            
            watch_list_id = result[0]
            
            # Remove analysis records
            cursor.execute('''
            DELETE FROM analysis_records 
            WHERE watch_list_id = ? AND ticker = ?
            ''', (watch_list_id, ticker))
            
            # Update watch list updated_date
            cursor.execute('''
            UPDATE watch_lists SET updated_date = ? WHERE id = ?
            ''', (datetime.now().isoformat(), watch_list_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Removed {ticker} from watch list '{watch_list_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error removing {ticker} from watch list '{watch_list_name}': {e}")
            return False
    
    def delete_watch_list(self, name: str) -> bool:
        """
        Delete a watch list and all its analysis records
        
        Args:
            name (str): Watch list name
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get watch list ID
            cursor.execute('SELECT id FROM watch_lists WHERE name = ?', (name,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Watch list '{name}' not found")
                conn.close()
                return False
            
            watch_list_id = result[0]
            
            # Delete analysis records first (foreign key constraint)
            cursor.execute('DELETE FROM analysis_records WHERE watch_list_id = ?', (watch_list_id,))
            
            # Delete watch list
            cursor.execute('DELETE FROM watch_lists WHERE id = ?', (watch_list_id,))
            
            conn.commit()
            conn.close()
            
            # Remove from JSON backup
            try:
                with open(self.json_file, 'r') as f:
                    data = json.load(f)
                
                if name in data["watch_lists"]:
                    del data["watch_lists"][name]
                    
                    with open(self.json_file, 'w') as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                logger.warning(f"Could not update JSON backup: {e}")
            
            logger.info(f"Deleted watch list: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting watch list '{name}': {e}")
            return False
    
    def export_watch_list_to_csv(self, watch_list_name: str, output_dir: str = None) -> Optional[str]:
        """
        Export watch list to CSV file
        
        Args:
            watch_list_name (str): Watch list name
            output_dir (str): Output directory (default: use configured export directory)
            
        Returns:
            str: Path to exported file or None if failed
        """
        try:
            watch_list = self.get_watch_list(watch_list_name)
            if not watch_list:
                logger.error(f"Watch list '{watch_list_name}' not found")
                return None
            
            # Use configured export directory if none specified
            if output_dir is None:
                output_dir = ensure_export_directory()
                if output_dir is None:
                    logger.error("No usable export directory available")
                    return None
            
            # Create output directory
            output_path = Path(output_dir)
            if not output_path.exists():
                try:
                    output_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to create export directory '{output_dir}': {e}")
                    return None
            
            # Prepare data for CSV
            csv_data = []
            for stock in watch_list['stocks']:
                csv_data.append({
                    'Ticker': stock['ticker'],
                    'Company Name': stock['company_name'],
                    'Analysis Date': stock['analysis_date'],
                    'Current Price': stock['current_price'],
                    'Fair Value': stock['fair_value'],
                    'Upside/Downside %': stock['upside_downside_pct'],
                    'Discount Rate': stock['discount_rate'],
                    'Terminal Growth Rate': stock['terminal_growth_rate'],
                    'FCF Type': stock['fcf_type']
                })
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(csv_data)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{watch_list_name.replace(' ', '_')}_{timestamp}.csv"
            filepath = output_path / filename
            
            df.to_csv(filepath, index=False)
            
            logger.info(f"Exported watch list '{watch_list_name}' to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting watch list '{watch_list_name}': {e}")
            return None
    
    def get_stock_performance_summary(self, watch_list_name: str) -> Optional[Dict]:
        """
        Get performance summary for stocks in a watch list
        
        Args:
            watch_list_name (str): Watch list name
            
        Returns:
            dict: Performance summary statistics
        """
        try:
            watch_list = self.get_watch_list(watch_list_name)
            if not watch_list or not watch_list['stocks']:
                return None
            
            upside_values = [stock['upside_downside_pct'] for stock in watch_list['stocks'] 
                           if stock['upside_downside_pct'] is not None]
            
            if not upside_values:
                return None
            
            summary = {
                'total_stocks': len(watch_list['stocks']),
                'avg_upside_downside': sum(upside_values) / len(upside_values),
                'max_upside': max(upside_values),
                'min_upside': min(upside_values),
                'undervalued_count': len([v for v in upside_values if v > 0]),
                'overvalued_count': len([v for v in upside_values if v < 0]),
                'fairly_valued_count': len([v for v in upside_values if abs(v) <= 5])
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary for '{watch_list_name}': {e}")
            return None
    
    def get_stock_analysis_history(self, watch_list_name: str, ticker: str = None) -> Optional[Dict]:
        """
        Get historical analysis data for a specific stock or all stocks in watch list
        
        Args:
            watch_list_name (str): Watch list name
            ticker (str): Specific ticker symbol (optional, if None returns all)
            
        Returns:
            dict: Historical analysis data
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get watch list ID
            cursor.execute('SELECT id FROM watch_lists WHERE name = ?', (watch_list_name,))
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"Watch list '{watch_list_name}' not found")
                conn.close()
                return None
            
            watch_list_id = result[0]
            
            # Build query based on whether ticker is specified
            if ticker:
                cursor.execute('''
                SELECT ticker, company_name, analysis_date, current_price, fair_value,
                       discount_rate, terminal_growth_rate, upside_downside_pct, fcf_type,
                       dcf_assumptions, analysis_metadata
                FROM analysis_records 
                WHERE watch_list_id = ? AND ticker = ?
                ORDER BY analysis_date DESC
                ''', (watch_list_id, ticker))
            else:
                cursor.execute('''
                SELECT ticker, company_name, analysis_date, current_price, fair_value,
                       discount_rate, terminal_growth_rate, upside_downside_pct, fcf_type,
                       dcf_assumptions, analysis_metadata
                FROM analysis_records 
                WHERE watch_list_id = ?
                ORDER BY ticker, analysis_date DESC
                ''', (watch_list_id,))
            
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                return {
                    'watch_list_name': watch_list_name,
                    'ticker': ticker,
                    'history': []
                }
            
            # Organize data
            history = []
            for record in records:
                history_item = {
                    "ticker": record[0],
                    "company_name": record[1],
                    "analysis_date": record[2],
                    "current_price": record[3],
                    "fair_value": record[4],
                    "discount_rate": record[5],
                    "terminal_growth_rate": record[6],
                    "upside_downside_pct": record[7],
                    "fcf_type": record[8],
                    "dcf_assumptions": json.loads(record[9]) if record[9] else {},
                    "analysis_metadata": json.loads(record[10]) if record[10] else {}
                }
                history.append(history_item)
            
            return {
                'watch_list_name': watch_list_name,
                'ticker': ticker,
                'history': history,
                'total_records': len(history)
            }
            
        except Exception as e:
            logger.error(f"Error getting stock history for '{ticker}' in '{watch_list_name}': {e}")
            return None
    
    def export_stock_history_to_csv(self, watch_list_name: str, ticker: str = None, 
                                   output_dir: str = None) -> Optional[str]:
        """
        Export stock analysis history to CSV file
        
        Args:
            watch_list_name (str): Watch list name
            ticker (str): Specific ticker (optional, if None exports all stocks)
            output_dir (str): Output directory (default: use configured export directory)
            
        Returns:
            str: Path to exported file or None if failed
        """
        try:
            history_data = self.get_stock_analysis_history(watch_list_name, ticker)
            if not history_data or not history_data['history']:
                logger.error(f"No history data found for {ticker or 'all stocks'} in '{watch_list_name}'")
                return None
            
            # Use configured export directory if none specified
            if output_dir is None:
                output_dir = ensure_export_directory()
                if output_dir is None:
                    logger.error("No usable export directory available")
                    return None
            
            # Create output directory
            output_path = Path(output_dir)
            if not output_path.exists():
                try:
                    output_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to create export directory '{output_dir}': {e}")
                    return None
            
            # Prepare data for CSV
            csv_data = []
            for analysis in history_data['history']:
                csv_data.append({
                    'Ticker': analysis['ticker'],
                    'Company Name': analysis['company_name'],
                    'Analysis Date': analysis['analysis_date'][:19] if analysis['analysis_date'] else 'N/A',  # Remove microseconds
                    'Current Price': analysis['current_price'],
                    'Fair Value': analysis['fair_value'],
                    'Upside/Downside %': analysis['upside_downside_pct'],
                    'Discount Rate': analysis['discount_rate'],
                    'Terminal Growth Rate': analysis['terminal_growth_rate'],
                    'FCF Type': analysis['fcf_type']
                })
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(csv_data)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if ticker:
                filename = f"{watch_list_name.replace(' ', '_')}_{ticker}_history_{timestamp}.csv"
            else:
                filename = f"{watch_list_name.replace(' ', '_')}_full_history_{timestamp}.csv"
            
            filepath = output_path / filename
            df.to_csv(filepath, index=False)
            
            logger.info(f"Exported history for {ticker or 'all stocks'} to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting history for {ticker or 'all stocks'}: {e}")
            return None
    
    def copy_stock_to_watch_list(self, source_watch_list: str, target_watch_list: str, 
                                ticker: str, copy_latest_only: bool = True) -> bool:
        """
        Copy a stock from one watch list to another (allows multi-list membership)
        
        Args:
            source_watch_list (str): Source watch list name
            target_watch_list (str): Target watch list name
            ticker (str): Stock ticker to copy
            copy_latest_only (bool): If True, copies only latest analysis; if False, copies all history
            
        Returns:
            bool: True if copied successfully
        """
        try:
            # Get source stock data
            source_history = self.get_stock_analysis_history(source_watch_list, ticker)
            if not source_history or not source_history['history']:
                logger.error(f"No data found for {ticker} in '{source_watch_list}'")
                return False
            
            # Get target watch list ID
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM watch_lists WHERE name = ?', (target_watch_list,))
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"Target watch list '{target_watch_list}' not found")
                conn.close()
                return False
            
            target_watch_list_id = result[0]
            
            # Determine which analyses to copy
            analyses_to_copy = source_history['history']
            if copy_latest_only:
                analyses_to_copy = [source_history['history'][0]]  # Most recent first
            
            # Copy each analysis
            copied_count = 0
            for analysis in analyses_to_copy:
                cursor.execute('''
                INSERT INTO analysis_records 
                (watch_list_id, ticker, company_name, analysis_date, current_price, 
                 fair_value, discount_rate, terminal_growth_rate, upside_downside_pct, 
                 fcf_type, dcf_assumptions, analysis_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    target_watch_list_id,
                    analysis['ticker'],
                    analysis['company_name'],
                    analysis['analysis_date'],
                    analysis['current_price'],
                    analysis['fair_value'],
                    analysis['discount_rate'],
                    analysis['terminal_growth_rate'],
                    analysis['upside_downside_pct'],
                    analysis['fcf_type'],
                    json.dumps(analysis['dcf_assumptions']),
                    json.dumps(analysis['analysis_metadata'])
                ))
                copied_count += 1
            
            # Update target watch list updated_date
            cursor.execute('''
            UPDATE watch_lists SET updated_date = ? WHERE id = ?
            ''', (datetime.now().isoformat(), target_watch_list_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Copied {copied_count} analyses for {ticker} from '{source_watch_list}' to '{target_watch_list}'")
            return True
            
        except Exception as e:
            logger.error(f"Error copying {ticker} from '{source_watch_list}' to '{target_watch_list}': {e}")
            return False
    
    def get_watch_lists_containing_stock(self, ticker: str) -> List[Dict]:
        """
        Get all watch lists that contain a specific stock
        
        Args:
            ticker (str): Stock ticker to search for
            
        Returns:
            list: List of watch list info dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT DISTINCT wl.name, wl.description, wl.created_date, wl.updated_date,
                   COUNT(ar.id) as analysis_count,
                   MAX(ar.analysis_date) as latest_analysis
            FROM watch_lists wl
            INNER JOIN analysis_records ar ON wl.id = ar.watch_list_id
            WHERE ar.ticker = ?
            GROUP BY wl.id, wl.name, wl.description, wl.created_date, wl.updated_date
            ORDER BY wl.updated_date DESC
            ''', (ticker,))
            
            results = cursor.fetchall()
            conn.close()
            
            watch_lists = []
            for result in results:
                watch_lists.append({
                    "name": result[0],
                    "description": result[1],
                    "created_date": result[2],
                    "updated_date": result[3],
                    "analysis_count": result[4],
                    "latest_analysis": result[5]
                })
            
            return watch_lists
            
        except Exception as e:
            logger.error(f"Error getting watch lists containing {ticker}: {e}")
            return []
    
    def move_stock_between_lists(self, source_watch_list: str, target_watch_list: str, 
                                ticker: str, move_all_history: bool = True) -> bool:
        """
        Move a stock from one watch list to another (removes from source)
        
        Args:
            source_watch_list (str): Source watch list name
            target_watch_list (str): Target watch list name
            ticker (str): Stock ticker to move
            move_all_history (bool): If True, moves all history; if False, moves latest only
            
        Returns:
            bool: True if moved successfully
        """
        try:
            # First copy the stock
            copy_success = self.copy_stock_to_watch_list(
                source_watch_list, target_watch_list, ticker, 
                copy_latest_only=not move_all_history
            )
            
            if not copy_success:
                return False
            
            # Then remove from source
            remove_success = self.remove_stock_from_watch_list(source_watch_list, ticker)
            
            if remove_success:
                logger.info(f"Successfully moved {ticker} from '{source_watch_list}' to '{target_watch_list}'")
            else:
                logger.warning(f"Copied {ticker} to '{target_watch_list}' but failed to remove from '{source_watch_list}'")
            
            return remove_success
            
        except Exception as e:
            logger.error(f"Error moving {ticker} from '{source_watch_list}' to '{target_watch_list}': {e}")
            return False
    
    def get_stock_membership_summary(self, ticker: str) -> Optional[Dict]:
        """
        Get a summary of which watch lists contain a specific stock
        
        Args:
            ticker (str): Stock ticker
            
        Returns:
            dict: Summary information about stock's watch list memberships
        """
        try:
            watch_lists = self.get_watch_lists_containing_stock(ticker)
            
            if not watch_lists:
                return {
                    'ticker': ticker,
                    'total_lists': 0,
                    'watch_lists': [],
                    'latest_analysis_date': None,
                    'total_analyses': 0
                }
            
            total_analyses = sum(wl['analysis_count'] for wl in watch_lists)
            latest_date = max(wl['latest_analysis'] for wl in watch_lists if wl['latest_analysis'])
            
            return {
                'ticker': ticker,
                'total_lists': len(watch_lists),
                'watch_lists': watch_lists,
                'latest_analysis_date': latest_date,
                'total_analyses': total_analyses
            }
            
        except Exception as e:
            logger.error(f"Error getting membership summary for {ticker}: {e}")
            return None