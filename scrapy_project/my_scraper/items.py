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
    transformers_variations = scrapy.Field()  # List of TransformersVariationItem
    model_metadata = scrapy.Field()  # Array containing collaborators and other metadata
    scraped_on = scrapy.Field()  # Timestamp when data was scraped


class TransformersVariationItem(scrapy.Item):
    """Item for Transformers variation metadata"""
    transformers_variation = scrapy.Field()
    transformers_variation_name = scrapy.Field()
    transformers_variation_version = scrapy.Field()
    transformers_variation_license = scrapy.Field()
    transformers_variation_downloads = scrapy.Field()
    transformers_model_card = scrapy.Field()
    transformers_is_finetunable = scrapy.Field()
