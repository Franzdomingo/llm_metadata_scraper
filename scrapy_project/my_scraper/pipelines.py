"""
Item pipelines for processing scraped data

This module contains pipelines for:
- Data cleaning and validation
- Export to JSON
- Export to CSV
"""

import json
import csv
import os
import logging
from datetime import datetime
from itemadapter import ItemAdapter
from my_scraper.utils import clean_text


class DataCleaningPipeline:
    """
    Pipeline to clean and validate scraped data
    """
    
    def process_item(self, item, spider):
        """
        Clean item data
        
        Args:
            item: Scraped item
            spider: Spider instance
            
        Returns:
            Cleaned item
        """
        adapter = ItemAdapter(item)
        
        # Clean text fields
        text_fields = ['name', 'short_description', 'downloads', 'tags', 'model_card']
        
        for field in text_fields:
            if field in adapter:
                value = adapter.get(field)
                if isinstance(value, str):
                    adapter[field] = clean_text(value)
        
        return item


class JsonExportPipeline:
    """
    Pipeline to export items to JSON file
    """
    
    def __init__(self):
        self.items = []
        self.file = None
        
    def open_spider(self, spider):
        """Initialize when spider opens"""
        # Create output directory if it doesn't exist
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{output_dir}/{spider.name}_{timestamp}.json'
        
        logging.info(f'Opening JSON export file: {filename}')
        self.file = open(filename, 'w', encoding='utf-8')
        self.items = []
    
    def close_spider(self, spider):
        """Write data and close file when spider closes"""
        if self.file:
            # Write all items as pretty-printed JSON
            json.dump(self.items, self.file, ensure_ascii=False, indent=2)
            self.file.close()
            logging.info(f'Saved {len(self.items)} items to JSON')
    
    def process_item(self, item, spider):
        """Add item to list"""
        self.items.append(dict(item))
        return item


class CsvExportPipeline:
    """
    Pipeline to export items to CSV file
    """
    
    def __init__(self):
        self.file = None
        self.writer = None
        self.fields = None
        
    def open_spider(self, spider):
        """Initialize when spider opens"""
        # Create output directory if it doesn't exist
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{output_dir}/{spider.name}_{timestamp}.csv'
        
        logging.info(f'Opening CSV export file: {filename}')
        self.file = open(filename, 'w', newline='', encoding='utf-8')
    
    def close_spider(self, spider):
        """Close file when spider closes"""
        if self.file:
            self.file.close()
            logging.info(f'CSV export file closed')
    
    def process_item(self, item, spider):
        """Write item to CSV"""
        adapter = ItemAdapter(item)
        
        # Initialize writer with fields from first item
        if not self.writer:
            self.fields = list(adapter.keys())
            self.writer = csv.DictWriter(self.file, fieldnames=self.fields)
            self.writer.writeheader()
        
        # Write row
        self.writer.writerow(adapter.asdict())
        
        return item
