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
from typing import Dict, List, Optional, Any, Tuple, Union
import pandas as pd
from config import get_export_directory, get_export_config, ensure_export_directory

logger = logging.getLogger(__name__)

# Import price service integration
try:
    from ...data_sources.price_service_integration import (
        StreamlitPriceIntegration, 
        get_current_price_simple, 
        get_current_prices_simple
    )
    from ...data_sources.real_time_price_service import PriceData
    PRICE_SERVICE_AVAILABLE = True
except ImportError:
    logger.warning("Price service integration not available - price fetching methods will be disabled")
    PRICE_SERVICE_AVAILABLE = False


class WatchListManager:
    """
    Manages watch lists with analysis tracking capabilities
    """

    def __init__(self, data_dir: str = "data/watch_lists"):
        """
        Initialize watch list manager

        Args:
            data_dir (str): Directory to store watch list data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.json_file = self.data_dir / "watch_lists.json"
        self.db_file = self.data_dir / "watch_lists.db"
        self.preferences_file = self.data_dir / "user_preferences.json"

        # Initialize storage
        self._init_json_storage()
        self._init_sqlite_storage()
        self._init_preferences()
        
        # Initialize price service integration
        self._price_integration = None
        if PRICE_SERVICE_AVAILABLE:
            self._price_integration = StreamlitPriceIntegration()

    def _init_preferences(self):
        """Initialize user preferences storage"""
        if not self.preferences_file.exists():
            default_preferences = {
                "default_view": "current",  # "current" or "historical"
                "price_refresh_interval": 15,  # minutes
                "show_price_freshness": True,
                "auto_refresh_enabled": False,
                "created": datetime.now().isoformat()
            }
            with open(self.preferences_file, 'w') as f:
                json.dump(default_preferences, f, indent=2)

    def _init_json_storage(self):
        """Initialize JSON storage file if it doesn't exist"""
        if not self.json_file.exists():
            initial_data = {
                "watch_lists": {},
                "metadata": {"created": datetime.now().isoformat(), "version": "1.0"},
            }
            with open(self.json_file, 'w') as f:
                json.dump(initial_data, f, indent=2)

    def _init_sqlite_storage(self):
        """Initialize SQLite database for watch lists"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Create watch_lists table
        cursor.execute(
            '''
        CREATE TABLE IF NOT EXISTS watch_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_date TEXT NOT NULL,
            updated_date TEXT NOT NULL
        )
        '''
        )

        # Create analysis_records table
        cursor.execute(
            '''
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
            pb_ratio REAL,
            book_value_per_share REAL,
            pb_industry_median REAL,
            pb_valuation_fair REAL,
            pb_analysis_data TEXT,
            FOREIGN KEY (watch_list_id) REFERENCES watch_lists (id)
        )
        '''
        )

        # Add P/B columns to existing tables if they don't exist
        try:
            cursor.execute('ALTER TABLE analysis_records ADD COLUMN pb_ratio REAL')
        except:
            pass  # Column already exists
        try:
            cursor.execute('ALTER TABLE analysis_records ADD COLUMN book_value_per_share REAL')
        except:
            pass  # Column already exists
        try:
            cursor.execute('ALTER TABLE analysis_records ADD COLUMN pb_industry_median REAL')
        except:
            pass  # Column already exists
        try:
            cursor.execute('ALTER TABLE analysis_records ADD COLUMN pb_valuation_fair REAL')
        except:
            pass  # Column already exists
        try:
            cursor.execute('ALTER TABLE analysis_records ADD COLUMN pb_analysis_data TEXT')
        except:
            pass  # Column already exists
        try:
            cursor.execute(
                'ALTER TABLE analysis_records ADD COLUMN analysis_type TEXT DEFAULT "DCF"'
            )
        except:
            pass  # Column already exists

        # Create index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON analysis_records (ticker)')
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_records (analysis_date)'
        )

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
            cursor.execute(
                '''
            INSERT INTO watch_lists (name, description, created_date, updated_date)
            VALUES (?, ?, ?, ?)
            ''',
                (name, description, current_time, current_time),
            )

            conn.commit()
            conn.close()

            # Add to JSON as backup
            with open(self.json_file, 'r') as f:
                data = json.load(f)

            data["watch_lists"][name] = {
                "description": description,
                "created_date": current_time,
                "updated_date": current_time,
                "stocks": [],
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
                    cursor.execute(
                        '''
                    SELECT ar.ticker, ar.company_name, ar.analysis_date, ar.current_price, ar.fair_value,
                           ar.discount_rate, ar.terminal_growth_rate, ar.upside_downside_pct, ar.fcf_type,
                           ar.dcf_assumptions, ar.analysis_metadata, ar.analysis_type
                    FROM analysis_records ar
                    INNER JOIN (
                        SELECT ticker, MAX(analysis_date) as latest_date
                        FROM analysis_records 
                        WHERE watch_list_id = ?
                        GROUP BY ticker
                    ) latest ON ar.ticker = latest.ticker AND ar.analysis_date = latest.latest_date
                    WHERE ar.watch_list_id = ?
                    ORDER BY ar.analysis_date DESC
                    ''',
                        (watch_list_id, watch_list_id),
                    )
                else:
                    # Get all analysis records
                    cursor.execute(
                        '''
                    SELECT ticker, company_name, analysis_date, current_price, fair_value,
                           discount_rate, terminal_growth_rate, upside_downside_pct, fcf_type,
                           dcf_assumptions, analysis_metadata, analysis_type
                    FROM analysis_records 
                    WHERE watch_list_id = ?
                    ORDER BY analysis_date DESC
                    ''',
                        (watch_list_id,),
                    )

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
                        "analysis_metadata": json.loads(record[10]) if record[10] else {},
                        "analysis_type": record[11] if len(record) > 11 else "DCF",
                    }
                    stocks.append(stock_data)

                conn.close()

                return {
                    "name": name,
                    "description": description,
                    "created_date": created_date,
                    "updated_date": updated_date,
                    "stocks": stocks,
                    "latest_only": latest_only,
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

            cursor.execute(
                '''
            SELECT wl.name, wl.description, wl.created_date, wl.updated_date,
                   COUNT(ar.id) as stock_count
            FROM watch_lists wl
            LEFT JOIN analysis_records ar ON wl.id = ar.watch_list_id
            GROUP BY wl.id, wl.name, wl.description, wl.created_date, wl.updated_date
            ORDER BY wl.updated_date DESC
            '''
            )

            results = cursor.fetchall()
            conn.close()

            watch_lists = []
            for result in results:
                watch_lists.append(
                    {
                        "name": result[0],
                        "description": result[1],
                        "created_date": result[2],
                        "updated_date": result[3],
                        "stock_count": result[4],
                    }
                )

            return watch_lists

        except Exception as e:
            logger.error(f"Error listing watch lists: {e}")
            return []

    def get_all_watch_lists(self) -> Dict[str, Dict]:
        """
        Get all watch lists as a dictionary keyed by watch list name

        Returns:
            dict: Dictionary of watch list name -> watch list data
        """
        try:
            watch_lists = self.list_watch_lists()
            
            result = {}
            for watch_list in watch_lists:
                result[watch_list['name']] = {
                    'description': watch_list['description'],
                    'created_date': watch_list['created_date'],
                    'updated_date': watch_list['updated_date'],
                    'stock_count': watch_list['stock_count']
                }
            
            return result

        except Exception as e:
            logger.error(f"Error getting all watch lists: {e}")
            return {}

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
            analysis_type = analysis_data.get('analysis_type', 'DCF')

            # Extract P/B analysis data if available
            pb_data = analysis_data.get('pb_analysis', {})
            pb_ratio = None
            book_value_per_share = None
            pb_industry_median = None
            pb_valuation_fair = None
            pb_analysis_data = None

            if pb_data:
                current_data = pb_data.get('current_data', {})
                pb_ratio = current_data.get('pb_ratio')
                book_value_per_share = current_data.get('book_value_per_share')

                industry_comp = pb_data.get('industry_comparison', {})
                benchmarks = industry_comp.get('benchmarks', {})
                pb_industry_median = benchmarks.get('median')

                valuation_analysis = pb_data.get('valuation_analysis', {})
                valuation_ranges = valuation_analysis.get('valuation_ranges', {})
                pb_valuation_fair = valuation_ranges.get('fair_value')

                pb_analysis_data = json.dumps(pb_data)

            # Insert analysis record
            cursor.execute(
                '''
            INSERT INTO analysis_records 
            (watch_list_id, ticker, company_name, analysis_date, current_price, 
             fair_value, discount_rate, terminal_growth_rate, upside_downside_pct, 
             fcf_type, dcf_assumptions, analysis_metadata, pb_ratio, book_value_per_share,
             pb_industry_median, pb_valuation_fair, pb_analysis_data, analysis_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
                (
                    watch_list_id,
                    ticker,
                    company_name,
                    analysis_date,
                    current_price,
                    fair_value,
                    discount_rate,
                    terminal_growth_rate,
                    upside_downside_pct,
                    fcf_type,
                    dcf_assumptions,
                    analysis_metadata,
                    pb_ratio,
                    book_value_per_share,
                    pb_industry_median,
                    pb_valuation_fair,
                    pb_analysis_data,
                    analysis_type,
                ),
            )

            # Update watch list updated_date
            cursor.execute(
                '''
            UPDATE watch_lists SET updated_date = ? WHERE id = ?
            ''',
                (analysis_date, watch_list_id),
            )

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
            cursor.execute(
                '''
            DELETE FROM analysis_records 
            WHERE watch_list_id = ? AND ticker = ?
            ''',
                (watch_list_id, ticker),
            )

            # Update watch list updated_date
            cursor.execute(
                '''
            UPDATE watch_lists SET updated_date = ? WHERE id = ?
            ''',
                (datetime.now().isoformat(), watch_list_id),
            )

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

    def export_watch_list_to_csv(
        self, watch_list_name: str, output_dir: str = None
    ) -> Optional[str]:
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
                csv_data.append(
                    {
                        'Ticker': stock['ticker'],
                        'Company Name': stock['company_name'],
                        'Analysis Date': stock['analysis_date'],
                        'Current Price': stock['current_price'],
                        'Fair Value': stock['fair_value'],
                        'Upside/Downside %': stock['upside_downside_pct'],
                        'Discount Rate': stock['discount_rate'],
                        'Terminal Growth Rate': stock['terminal_growth_rate'],
                        'FCF Type': stock['fcf_type'],
                    }
                )

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

            upside_values = [
                stock['upside_downside_pct']
                for stock in watch_list['stocks']
                if stock['upside_downside_pct'] is not None
            ]

            if not upside_values:
                return None

            summary = {
                'total_stocks': len(watch_list['stocks']),
                'avg_upside_downside': sum(upside_values) / len(upside_values),
                'max_upside': max(upside_values),
                'min_upside': min(upside_values),
                'undervalued_count': len([v for v in upside_values if v > 0]),
                'overvalued_count': len([v for v in upside_values if v < 0]),
                'fairly_valued_count': len([v for v in upside_values if abs(v) <= 5]),
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting performance summary for '{watch_list_name}': {e}")
            return None

    def get_stock_analysis_history(
        self, watch_list_name: str, ticker: str = None
    ) -> Optional[Dict]:
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
                cursor.execute(
                    '''
                SELECT ticker, company_name, analysis_date, current_price, fair_value,
                       discount_rate, terminal_growth_rate, upside_downside_pct, fcf_type,
                       dcf_assumptions, analysis_metadata, analysis_type
                FROM analysis_records 
                WHERE watch_list_id = ? AND ticker = ?
                ORDER BY analysis_date DESC
                ''',
                    (watch_list_id, ticker),
                )
            else:
                cursor.execute(
                    '''
                SELECT ticker, company_name, analysis_date, current_price, fair_value,
                       discount_rate, terminal_growth_rate, upside_downside_pct, fcf_type,
                       dcf_assumptions, analysis_metadata, analysis_type
                FROM analysis_records 
                WHERE watch_list_id = ?
                ORDER BY ticker, analysis_date DESC
                ''',
                    (watch_list_id,),
                )

            records = cursor.fetchall()
            conn.close()

            if not records:
                return {'watch_list_name': watch_list_name, 'ticker': ticker, 'history': []}

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
                    "analysis_metadata": json.loads(record[10]) if record[10] else {},
                    "analysis_type": record[11] if len(record) > 11 else "DCF",
                }
                history.append(history_item)

            return {
                'watch_list_name': watch_list_name,
                'ticker': ticker,
                'history': history,
                'total_records': len(history),
            }

        except Exception as e:
            logger.error(f"Error getting stock history for '{ticker}' in '{watch_list_name}': {e}")
            return None

    def export_stock_history_to_csv(
        self, watch_list_name: str, ticker: str = None, output_dir: str = None
    ) -> Optional[str]:
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
                logger.error(
                    f"No history data found for {ticker or 'all stocks'} in '{watch_list_name}'"
                )
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
                csv_data.append(
                    {
                        'Ticker': analysis['ticker'],
                        'Company Name': analysis['company_name'],
                        'Analysis Date': (
                            analysis['analysis_date'][:19] if analysis['analysis_date'] else 'N/A'
                        ),  # Remove microseconds
                        'Current Price': analysis['current_price'],
                        'Fair Value': analysis['fair_value'],
                        'Upside/Downside %': analysis['upside_downside_pct'],
                        'Discount Rate': analysis['discount_rate'],
                        'Terminal Growth Rate': analysis['terminal_growth_rate'],
                        'FCF Type': analysis['fcf_type'],
                    }
                )

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

    def copy_stock_to_watch_list(
        self,
        source_watch_list: str,
        target_watch_list: str,
        ticker: str,
        copy_latest_only: bool = True,
    ) -> bool:
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
                cursor.execute(
                    '''
                INSERT INTO analysis_records 
                (watch_list_id, ticker, company_name, analysis_date, current_price, 
                 fair_value, discount_rate, terminal_growth_rate, upside_downside_pct, 
                 fcf_type, dcf_assumptions, analysis_metadata, analysis_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                    (
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
                        json.dumps(analysis['analysis_metadata']),
                        analysis.get('analysis_type', 'DCF'),
                    ),
                )
                copied_count += 1

            # Update target watch list updated_date
            cursor.execute(
                '''
            UPDATE watch_lists SET updated_date = ? WHERE id = ?
            ''',
                (datetime.now().isoformat(), target_watch_list_id),
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Copied {copied_count} analyses for {ticker} from '{source_watch_list}' to '{target_watch_list}'"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error copying {ticker} from '{source_watch_list}' to '{target_watch_list}': {e}"
            )
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

            cursor.execute(
                '''
            SELECT DISTINCT wl.name, wl.description, wl.created_date, wl.updated_date,
                   COUNT(ar.id) as analysis_count,
                   MAX(ar.analysis_date) as latest_analysis
            FROM watch_lists wl
            INNER JOIN analysis_records ar ON wl.id = ar.watch_list_id
            WHERE ar.ticker = ?
            GROUP BY wl.id, wl.name, wl.description, wl.created_date, wl.updated_date
            ORDER BY wl.updated_date DESC
            ''',
                (ticker,),
            )

            results = cursor.fetchall()
            conn.close()

            watch_lists = []
            for result in results:
                watch_lists.append(
                    {
                        "name": result[0],
                        "description": result[1],
                        "created_date": result[2],
                        "updated_date": result[3],
                        "analysis_count": result[4],
                        "latest_analysis": result[5],
                    }
                )

            return watch_lists

        except Exception as e:
            logger.error(f"Error getting watch lists containing {ticker}: {e}")
            return []

    def move_stock_between_lists(
        self,
        source_watch_list: str,
        target_watch_list: str,
        ticker: str,
        move_all_history: bool = True,
    ) -> bool:
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
                source_watch_list, target_watch_list, ticker, copy_latest_only=not move_all_history
            )

            if not copy_success:
                return False

            # Then remove from source
            remove_success = self.remove_stock_from_watch_list(source_watch_list, ticker)

            if remove_success:
                logger.info(
                    f"Successfully moved {ticker} from '{source_watch_list}' to '{target_watch_list}'"
                )
            else:
                logger.warning(
                    f"Copied {ticker} to '{target_watch_list}' but failed to remove from '{source_watch_list}'"
                )

            return remove_success

        except Exception as e:
            logger.error(
                f"Error moving {ticker} from '{source_watch_list}' to '{target_watch_list}': {e}"
            )
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
                    'total_analyses': 0,
                }

            total_analyses = sum(wl['analysis_count'] for wl in watch_lists)
            latest_date = max(wl['latest_analysis'] for wl in watch_lists if wl['latest_analysis'])

            return {
                'ticker': ticker,
                'total_lists': len(watch_lists),
                'watch_lists': watch_lists,
                'latest_analysis_date': latest_date,
                'total_analyses': total_analyses,
            }

        except Exception as e:
            logger.error(f"Error getting membership summary for {ticker}: {e}")
            return None

    # ==================== ENHANCED PRICE FETCHING METHODS ====================

    def get_current_price(self, ticker: str, force_refresh: bool = False) -> Optional[float]:
        """
        Get current price for a single ticker
        
        Args:
            ticker (str): Stock ticker symbol
            force_refresh (bool): Force refresh from API sources
            
        Returns:
            float: Current price or None if unavailable
        """
        if not PRICE_SERVICE_AVAILABLE:
            logger.warning("Price service not available - cannot fetch current prices")
            return None
            
        try:
            if self._price_integration:
                price_data = self._price_integration.get_single_price_sync(ticker, force_refresh)
                return price_data.current_price if price_data else None
            else:
                return get_current_price_simple(ticker, use_cache=not force_refresh)
        except Exception as e:
            logger.error(f"Error fetching current price for {ticker}: {e}")
            return None

    def get_current_prices(self, tickers: List[str], force_refresh: bool = False) -> Dict[str, Optional[float]]:
        """
        Get current prices for multiple tickers
        
        Args:
            tickers (List[str]): List of stock ticker symbols
            force_refresh (bool): Force refresh from API sources
            
        Returns:
            Dict[str, Optional[float]]: Dictionary mapping tickers to prices
        """
        if not PRICE_SERVICE_AVAILABLE:
            logger.warning("Price service not available - cannot fetch current prices")
            return {ticker: None for ticker in tickers}
            
        try:
            if self._price_integration:
                prices_data = self._price_integration.get_prices_sync(tickers, force_refresh)
                return {
                    ticker: data.current_price if data else None
                    for ticker, data in prices_data.items()
                }
            else:
                return get_current_prices_simple(tickers, use_cache=not force_refresh)
        except Exception as e:
            logger.error(f"Error fetching current prices for {tickers}: {e}")
            return {ticker: None for ticker in tickers}

    def get_detailed_price_data(self, ticker: str, force_refresh: bool = False) -> Optional[PriceData]:
        """
        Get detailed price data including volume, market cap, and metadata
        
        Args:
            ticker (str): Stock ticker symbol  
            force_refresh (bool): Force refresh from API sources
            
        Returns:
            PriceData: Detailed price data or None if unavailable
        """
        if not PRICE_SERVICE_AVAILABLE or not self._price_integration:
            logger.warning("Price service not available - cannot fetch detailed price data")
            return None
            
        try:
            return self._price_integration.get_single_price_sync(ticker, force_refresh)
        except Exception as e:
            logger.error(f"Error fetching detailed price data for {ticker}: {e}")
            return None

    def get_watch_list_with_current_prices(self, watch_list_name: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get watch list data enriched with current price information
        
        Args:
            watch_list_name (str): Watch list name
            force_refresh (bool): Force refresh prices from API
            
        Returns:
            Dict: Watch list data with current price information
        """
        try:
            # Get base watch list data
            watch_list = self.get_watch_list(watch_list_name)
            if not watch_list:
                return None
                
            # Extract unique tickers
            tickers = list(set(stock['ticker'] for stock in watch_list['stocks']))
            
            if not tickers or not PRICE_SERVICE_AVAILABLE:
                return watch_list
                
            # Fetch current prices
            current_prices = {}
            detailed_price_data = {}
            
            if self._price_integration:
                prices_data = self._price_integration.get_prices_sync(tickers, force_refresh)
                for ticker, price_data in prices_data.items():
                    if price_data:
                        current_prices[ticker] = price_data.current_price
                        detailed_price_data[ticker] = price_data
            
            # Enrich stock data with current prices
            for stock in watch_list['stocks']:
                ticker = stock['ticker']
                current_price = current_prices.get(ticker)
                detailed_data = detailed_price_data.get(ticker)
                
                # Add current price data
                stock['current_market_price'] = current_price
                stock['price_last_updated'] = detailed_data.last_updated.isoformat() if detailed_data else None
                stock['price_source'] = detailed_data.source if detailed_data else None
                stock['price_cache_hit'] = detailed_data.cache_hit if detailed_data else False
                
                # Calculate updated upside/downside if we have both current and fair value
                if current_price and stock.get('fair_value'):
                    stock['updated_upside_downside_pct'] = (
                        (stock['fair_value'] - current_price) / current_price * 100
                    )
                    
                # Add volume and market cap if available
                if detailed_data:
                    stock['current_volume'] = detailed_data.volume
                    stock['current_market_cap'] = detailed_data.market_cap
                    stock['current_change_percent'] = detailed_data.change_percent
                    
            # Add price metadata to watch list
            watch_list['price_data'] = {
                'has_current_prices': len(current_prices) > 0,
                'price_count': len([p for p in current_prices.values() if p is not None]),
                'total_tickers': len(tickers),
                'last_price_update': datetime.now().isoformat(),
                'force_refresh_used': force_refresh
            }
            
            return watch_list
            
        except Exception as e:
            logger.error(f"Error enriching watch list '{watch_list_name}' with current prices: {e}")
            return self.get_watch_list(watch_list_name)  # Fallback to original data

    def get_user_preferences(self) -> Dict[str, Any]:
        """
        Get user preferences for watch list display and behavior
        
        Returns:
            Dict[str, Any]: User preferences
        """
        try:
            with open(self.preferences_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading user preferences: {e}")
            return {
                "default_view": "current",
                "price_refresh_interval": 15,
                "show_price_freshness": True,
                "auto_refresh_enabled": False
            }

    def set_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        Set user preferences for watch list display and behavior
        
        Args:
            preferences (Dict[str, Any]): Preferences to update
            
        Returns:
            bool: True if successful
        """
        try:
            current_prefs = self.get_user_preferences()
            current_prefs.update(preferences)
            current_prefs['updated'] = datetime.now().isoformat()
            
            with open(self.preferences_file, 'w') as f:
                json.dump(current_prefs, f, indent=2)
                
            logger.info(f"Updated user preferences: {list(preferences.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting user preferences: {e}")
            return False

    def get_price_performance_comparison(self, watch_list_name: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Compare current prices with historical analysis for performance tracking
        
        Args:
            watch_list_name (str): Watch list name
            force_refresh (bool): Force refresh prices from API
            
        Returns:
            Dict: Performance comparison data
        """
        try:
            # Get watch list with current prices
            enriched_watch_list = self.get_watch_list_with_current_prices(watch_list_name, force_refresh)
            if not enriched_watch_list or not enriched_watch_list.get('stocks'):
                return None
                
            comparisons = []
            for stock in enriched_watch_list['stocks']:
                ticker = stock['ticker']
                
                # Historical analysis data
                historical_price = stock.get('current_price', 0)  # Price at time of analysis
                fair_value = stock.get('fair_value', 0)
                original_upside = stock.get('upside_downside_pct', 0)
                
                # Current market data
                current_price = stock.get('current_market_price', 0)
                updated_upside = stock.get('updated_upside_downside_pct', 0)
                
                if historical_price and current_price and fair_value:
                    # Calculate performance metrics
                    price_change_pct = ((current_price - historical_price) / historical_price * 100)
                    
                    # Calculate how close we are to fair value
                    distance_to_fair_value = abs(current_price - fair_value) / fair_value * 100
                    
                    comparison = {
                        'ticker': ticker,
                        'company_name': stock.get('company_name', ''),
                        'analysis_date': stock.get('analysis_date'),
                        'historical_price': historical_price,
                        'current_price': current_price,
                        'fair_value': fair_value,
                        'price_change_pct': price_change_pct,
                        'original_upside_pct': original_upside,
                        'updated_upside_pct': updated_upside,
                        'upside_change': updated_upside - original_upside,
                        'distance_to_fair_value_pct': distance_to_fair_value,
                        'valuation_status': self._get_valuation_status(updated_upside),
                        'price_trend': 'up' if price_change_pct > 0 else 'down' if price_change_pct < 0 else 'flat'
                    }
                    comparisons.append(comparison)
            
            # Calculate summary statistics
            if comparisons:
                price_changes = [c['price_change_pct'] for c in comparisons if c['price_change_pct'] is not None]
                upside_values = [c['updated_upside_pct'] for c in comparisons if c['updated_upside_pct'] is not None]
                
                summary = {
                    'total_stocks': len(comparisons),
                    'avg_price_change_pct': sum(price_changes) / len(price_changes) if price_changes else 0,
                    'positive_movers': len([c for c in comparisons if c['price_change_pct'] > 0]),
                    'negative_movers': len([c for c in comparisons if c['price_change_pct'] < 0]),
                    'avg_current_upside_pct': sum(upside_values) / len(upside_values) if upside_values else 0,
                    'undervalued_count': len([c for c in comparisons if c['updated_upside_pct'] > 5]),
                    'overvalued_count': len([c for c in comparisons if c['updated_upside_pct'] < -5]),
                    'fairly_valued_count': len([c for c in comparisons if abs(c['updated_upside_pct']) <= 5]),
                }
            else:
                summary = {}
            
            return {
                'watch_list_name': watch_list_name,
                'comparison_date': datetime.now().isoformat(),
                'comparisons': comparisons,
                'summary': summary,
                'has_price_data': enriched_watch_list.get('price_data', {}).get('has_current_prices', False)
            }
            
        except Exception as e:
            logger.error(f"Error generating price performance comparison for '{watch_list_name}': {e}")
            return None

    def get_current_vs_historical_upside_downside(self, watch_list_name: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Calculate current vs historical upside/downside analysis for watch list
        This is the core implementation for Task #83
        
        Args:
            watch_list_name (str): Watch list name
            force_refresh (bool): Force refresh prices from API
            
        Returns:
            Dict: Current vs historical upside/downside comparison data
        """
        try:
            # Get watch list with current prices
            enriched_watch_list = self.get_watch_list_with_current_prices(watch_list_name, force_refresh)
            if not enriched_watch_list or not enriched_watch_list.get('stocks'):
                return None
                
            current_vs_historical = []
            
            for stock in enriched_watch_list['stocks']:
                ticker = stock['ticker']
                company_name = stock.get('company_name', '')
                analysis_date = stock.get('analysis_date', '')
                
                # Historical analysis data (from stored analysis)
                historical_price = stock.get('current_price', 0)  # Price at time of analysis
                fair_value = stock.get('fair_value', 0)
                historical_upside = stock.get('upside_downside_pct', 0)
                
                # Current market data
                current_market_price = stock.get('current_market_price', 0)
                
                # Skip if we don't have essential data
                if not (historical_price and fair_value and current_market_price):
                    continue
                    
                # Calculate current upside/downside using current price vs stored fair value
                current_upside_pct = ((fair_value - current_market_price) / current_market_price * 100)
                
                # Calculate price movement since analysis
                price_change_pct = ((current_market_price - historical_price) / historical_price * 100)
                
                # Calculate upside change (how the upside potential has changed)
                upside_change_pct = current_upside_pct - historical_upside
                
                # Determine if the opportunity has improved or worsened
                opportunity_status = self._classify_opportunity_change(upside_change_pct, price_change_pct)
                
                # Calculate days since analysis
                days_since_analysis = self._calculate_days_since_analysis(analysis_date)
                
                # Create detailed comparison record
                comparison = {
                    'ticker': ticker,
                    'company_name': company_name,
                    'analysis_date': analysis_date,
                    'days_since_analysis': days_since_analysis,
                    
                    # Historical perspective (at time of analysis)
                    'historical': {
                        'price': historical_price,
                        'upside_pct': historical_upside,
                        'fair_value': fair_value,
                        'valuation_status': self._get_valuation_status(historical_upside)
                    },
                    
                    # Current perspective (live calculation)
                    'current': {
                        'price': current_market_price,
                        'upside_pct': current_upside_pct,
                        'fair_value': fair_value,  # Same fair value for comparison
                        'valuation_status': self._get_valuation_status(current_upside_pct)
                    },
                    
                    # Change analysis
                    'changes': {
                        'price_change_pct': price_change_pct,
                        'upside_change_pct': upside_change_pct,
                        'opportunity_status': opportunity_status,
                        'price_trend': 'up' if price_change_pct > 0 else 'down' if price_change_pct < 0 else 'flat'
                    },
                    
                    # Investment implications
                    'investment_insight': self._generate_investment_insight(
                        historical_upside, current_upside_pct, price_change_pct, days_since_analysis
                    ),
                    
                    # Additional metadata
                    'price_data_source': stock.get('price_source', 'Unknown'),
                    'price_last_updated': stock.get('price_last_updated'),
                    'cache_hit': stock.get('price_cache_hit', False)
                }
                
                current_vs_historical.append(comparison)
            
            # Calculate aggregate statistics
            summary_stats = self._calculate_comparison_summary(current_vs_historical)
            
            return {
                'watch_list_name': watch_list_name,
                'analysis_date': datetime.now().isoformat(),
                'total_stocks': len(current_vs_historical),
                'stocks_with_data': len(current_vs_historical),
                'price_data_available': enriched_watch_list.get('price_data', {}).get('has_current_prices', False),
                'force_refresh_used': force_refresh,
                'comparisons': current_vs_historical,
                'summary': summary_stats
            }
            
        except Exception as e:
            logger.error(f"Error generating current vs historical upside/downside for '{watch_list_name}': {e}")
            return None

    def _classify_opportunity_change(self, upside_change_pct: float, price_change_pct: float) -> str:
        """
        Classify how the investment opportunity has changed
        
        Args:
            upside_change_pct (float): Change in upside percentage
            price_change_pct (float): Price change percentage
            
        Returns:
            str: Opportunity status classification
        """
        if upside_change_pct > 10:
            return "Opportunity Improved" if price_change_pct < 0 else "Fair Value Increased"
        elif upside_change_pct > 5:
            return "Slight Improvement"
        elif upside_change_pct > -5:
            return "Opportunity Unchanged"
        elif upside_change_pct > -10:
            return "Slight Deterioration"
        else:
            return "Opportunity Deteriorated" if price_change_pct > 0 else "Price Outpaced Value"

    def _calculate_days_since_analysis(self, analysis_date: str) -> Optional[int]:
        """
        Calculate days since analysis was performed
        
        Args:
            analysis_date (str): ISO format date string
            
        Returns:
            int: Days since analysis or None if invalid date
        """
        try:
            if not analysis_date:
                return None
            # Parse ISO date string
            analysis_datetime = datetime.fromisoformat(analysis_date.replace('Z', '+00:00'))
            current_datetime = datetime.now(analysis_datetime.tzinfo) if analysis_datetime.tzinfo else datetime.now()
            return (current_datetime - analysis_datetime).days
        except Exception:
            return None

    def _generate_investment_insight(self, historical_upside: float, current_upside: float, 
                                   price_change: float, days_since: Optional[int]) -> str:
        """
        Generate investment insight based on analysis changes
        
        Args:
            historical_upside (float): Original upside percentage
            current_upside (float): Current upside percentage  
            price_change (float): Price change percentage
            days_since (int): Days since analysis
            
        Returns:
            str: Investment insight text
        """
        time_context = f" over {days_since} days" if days_since else ""
        
        if current_upside > 20 and current_upside > historical_upside:
            return f"Strong buy opportunity - upside increased from {historical_upside:.1f}% to {current_upside:.1f}%{time_context}"
        elif current_upside > 20:
            return f"Strong buy maintained - {current_upside:.1f}% upside potential{time_context}"
        elif current_upside > 10 and price_change < -5:
            return f"Buy opportunity - price declined {abs(price_change):.1f}% while maintaining {current_upside:.1f}% upside{time_context}"
        elif current_upside < -10 and historical_upside > 10:
            return f"Opportunity lost - upside fell from {historical_upside:.1f}% to {current_upside:.1f}%{time_context}"
        elif abs(current_upside) <= 5:
            return f"Fair value reached - upside now {current_upside:.1f}%{time_context}"
        elif current_upside < historical_upside and price_change > 10:
            return f"Price appreciation reduced upside from {historical_upside:.1f}% to {current_upside:.1f}%{time_context}"
        else:
            return f"Monitor - upside changed from {historical_upside:.1f}% to {current_upside:.1f}%{time_context}"

    def _calculate_comparison_summary(self, comparisons: List[Dict]) -> Dict:
        """
        Calculate summary statistics for current vs historical comparison
        
        Args:
            comparisons (List[Dict]): List of comparison records
            
        Returns:
            Dict: Summary statistics
        """
        if not comparisons:
            return {}
            
        try:
            # Extract values for calculations
            current_upsides = [c['current']['upside_pct'] for c in comparisons]
            historical_upsides = [c['historical']['upside_pct'] for c in comparisons]
            upside_changes = [c['changes']['upside_change_pct'] for c in comparisons]
            price_changes = [c['changes']['price_change_pct'] for c in comparisons]
            
            # Calculate averages
            avg_current_upside = sum(current_upsides) / len(current_upsides)
            avg_historical_upside = sum(historical_upsides) / len(historical_upsides)
            avg_upside_change = sum(upside_changes) / len(upside_changes)
            avg_price_change = sum(price_changes) / len(price_changes)
            
            # Count opportunity categories
            opportunity_counts = {}
            for comparison in comparisons:
                status = comparison['changes']['opportunity_status']
                opportunity_counts[status] = opportunity_counts.get(status, 0) + 1
            
            # Count valuation changes
            valuation_improved = len([c for c in comparisons 
                                    if c['current']['upside_pct'] > c['historical']['upside_pct']])
            valuation_deteriorated = len([c for c in comparisons 
                                        if c['current']['upside_pct'] < c['historical']['upside_pct']])
            valuation_unchanged = len(comparisons) - valuation_improved - valuation_deteriorated
            
            return {
                'averages': {
                    'current_upside_pct': avg_current_upside,
                    'historical_upside_pct': avg_historical_upside,
                    'upside_change_pct': avg_upside_change,
                    'price_change_pct': avg_price_change
                },
                'opportunity_distribution': opportunity_counts,
                'valuation_changes': {
                    'improved': valuation_improved,
                    'deteriorated': valuation_deteriorated,
                    'unchanged': valuation_unchanged
                },
                'current_investment_profile': {
                    'strong_buys': len([c for c in comparisons if c['current']['upside_pct'] > 20]),
                    'buys': len([c for c in comparisons if 10 <= c['current']['upside_pct'] <= 20]),
                    'holds': len([c for c in comparisons if -10 <= c['current']['upside_pct'] < 10]),
                    'sells': len([c for c in comparisons if c['current']['upside_pct'] < -10])
                },
                'price_movement_summary': {
                    'gainers': len([c for c in comparisons if c['changes']['price_change_pct'] > 0]),
                    'decliners': len([c for c in comparisons if c['changes']['price_change_pct'] < 0]),
                    'unchanged': len([c for c in comparisons if c['changes']['price_change_pct'] == 0])
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating comparison summary: {e}")
            return {}

    def _get_valuation_status(self, upside_pct: float) -> str:
        """
        Get valuation status based on upside percentage
        
        Args:
            upside_pct (float): Upside percentage
            
        Returns:
            str: Valuation status
        """
        if upside_pct > 20:
            return "Significantly Undervalued"
        elif upside_pct > 5:
            return "Undervalued"  
        elif upside_pct > -5:
            return "Fairly Valued"
        elif upside_pct > -20:
            return "Overvalued"
        else:
            return "Significantly Overvalued"

    def refresh_watch_list_prices(self, watch_list_name: str) -> bool:
        """
        Refresh all prices for a watch list (convenience method)
        
        Args:
            watch_list_name (str): Watch list name
            
        Returns:
            bool: True if refresh was successful
        """
        try:
            enriched_data = self.get_watch_list_with_current_prices(watch_list_name, force_refresh=True)
            success = enriched_data is not None and enriched_data.get('price_data', {}).get('has_current_prices', False)
            
            if success:
                logger.info(f"Successfully refreshed prices for watch list '{watch_list_name}'")
            else:
                logger.warning(f"Price refresh may have failed for watch list '{watch_list_name}'")
                
            return success
            
        except Exception as e:
            logger.error(f"Error refreshing prices for watch list '{watch_list_name}': {e}")
            return False

    def get_price_cache_status(self) -> Dict[str, Any]:
        """
        Get current price cache status from the price service
        
        Returns:
            Dict[str, Any]: Cache status information
        """
        if not PRICE_SERVICE_AVAILABLE or not self._price_integration:
            return {
                'available': False,
                'reason': 'Price service not available'
            }
            
        try:
            cache_status = self._price_integration.service.get_cache_status()
            cache_status['available'] = True
            return cache_status
        except Exception as e:
            logger.error(f"Error getting price cache status: {e}")
            return {
                'available': False,
                'error': str(e)
            }
