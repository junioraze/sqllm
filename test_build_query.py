import unittest
from database import build_query

class TestBuildQuery(unittest.TestCase):
    def test_cte_with_select_final(self):
        params = {
            'select': ['mes', 'ano_2023', 'ano_2024'],
            'cte': (
                'WITH cte_dados_anuais AS (\n'
                '  SELECT \n'
                '    EXTRACT(YEAR FROM dta_venda) AS ano,\n'
                '    EXTRACT(MONTH FROM dta_venda) AS mes,\n'
                '    SUM(val_total) AS valor_mensal\n'
                '  FROM `glinhares.delivery.drvy_VeiculosVendas`\n'
                '  WHERE EXTRACT(YEAR FROM dta_venda) IN (2023, 2024)\n'
                '  GROUP BY ano, mes\n'
                ')\n'
                'SELECT mes, \n'
                '       SUM(CASE WHEN ano = 2023 THEN valor_mensal ELSE 0 END) AS ano_2023,\n'
                '       SUM(CASE WHEN ano = 2024 THEN valor_mensal ELSE 0 END) AS ano_2024\n'
                'FROM cte_dados_anuais\n'
                'GROUP BY mes\n'
            ),
            'from_table': 'cte_dados_anuais',
            'order_by': ['mes']
        }
        result = build_query(params)
        self.assertIn('SELECT mes', result)
        self.assertIn('SUM(CASE WHEN ano = 2023', result)
        self.assertNotIn('SELECT mes, ano_2023, ano_2024 FROM cte_dados_anuais', result)
        self.assertTrue(result.strip().startswith('WITH cte_dados_anuais'))

if __name__ == '__main__':
    unittest.main()
