import unittest

from src.modules.selectors_config import get_selectors_for_site


class TestTransformerVariationSelectors(unittest.TestCase):
    def test_kaggle_transformers_variation_selectors_present(self):
        selectors = get_selectors_for_site('kaggle')
        # expected keys added for transformers variation
        self.assertIn('transformers_variation_action', selectors)
        self.assertIn('transformers_variation_item', selectors)

        # expected CSS selector values
        self.assertEqual(selectors['transformers_variation_action'], '.MuiSelect-iconOutlined')
        self.assertEqual(
            selectors['transformers_variation_item'],
            'li.MuiButtonBase-root:nth-child(1) > div:nth-child(1) > p:nth-child(1)'
        )


if __name__ == '__main__':
    unittest.main()
