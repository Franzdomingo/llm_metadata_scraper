"""
Item pipelines for processing scraped data

This module contains pipelines for:
- Data cleaning and validation
- Export to JSON
"""

import json
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
        text_fields = ['name', 'short_description', 'downloads', 'usability', 'tags', 'model_card']

        for field in text_fields:
            if field in adapter:
                value = adapter.get(field)
                if isinstance(value, str):
                    adapter[field] = clean_text(value)

        # Clean model_metadata if present
        if 'model_metadata' in adapter:
            metadata = adapter.get('model_metadata')
            if isinstance(metadata, dict):
                # Clean collaborators list if present
                if 'collaborators' in metadata and isinstance(metadata['collaborators'], list):
                    metadata['collaborators'] = [
                        clean_text(collab) if isinstance(collab, str) else collab
                        for collab in metadata['collaborators']
                    ]

                # Clean authors list if present
                if 'authors' in metadata and isinstance(metadata['authors'], list):
                    metadata['authors'] = [
                        clean_text(author) if isinstance(author, str) else author
                        for author in metadata['authors']
                    ]

                # Clean provenance text if present
                if 'provenance' in metadata and isinstance(metadata['provenance'], str):
                    metadata['provenance'] = clean_text(metadata['provenance'])

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

        self.filename = filename
        self.file = open(filename, 'w', encoding='utf-8')
        self.items = []
    
    def close_spider(self, spider):
        """Write data and close file when spider closes"""
        if self.file:
            # Write all items as pretty-printed JSON
            json.dump(self.items, self.file, ensure_ascii=False, indent=2)
            self.file.close()
            logging.info(f'Saved {len(self.items)} items to {self.filename}')
    
    def process_item(self, item, spider):
        """Add item to list"""
        self.items.append(dict(item))
        return item


