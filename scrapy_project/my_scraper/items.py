"""
Define here the models for your scraped items

See documentation in:
https://docs.scrapy.org/en/latest/topics/items.html
"""

import scrapy


class KaggleModelItem(scrapy.Item):
    """Item for Kaggle model links"""
    name = scrapy.Field()
    kaggle_url = scrapy.Field()


class KaggleMetadataItem(scrapy.Item):
    """Item for Kaggle model metadata"""
    model_id = scrapy.Field()
    name = scrapy.Field()
    kaggle_url = scrapy.Field()
    short_description = scrapy.Field()
    downloads = scrapy.Field()
    usability = scrapy.Field()
    model_card = scrapy.Field()
    tags = scrapy.Field()
    variations = scrapy.Field()  # List of TransformersVariationItem
    model_metadata = scrapy.Field()  # Array containing collaborators and other metadata
    scraped_on = scrapy.Field()  # Timestamp when data was scraped


class TransformersVariationItem(scrapy.Item):
    """Item for Transformers variation metadata"""
    variation = scrapy.Field()
    variation_name = scrapy.Field()
    variation_version = scrapy.Field()
    variation_license = scrapy.Field()
    variation_downloads = scrapy.Field()
    model_card = scrapy.Field()
    is_finetunable = scrapy.Field()
    example_usage = scrapy.Field()


class NvidiaModelItem(scrapy.Item):
    """Item for NVIDIA model metadata"""
    name = scrapy.Field()
    nvidia_url = scrapy.Field()
    tags = scrapy.Field()
    model_card = scrapy.Field()  # Model card content from /modelcard page
    scraped_on = scrapy.Field()  # Timestamp when data was scraped
