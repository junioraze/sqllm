"""
SQL Validator v2 - Validação 360° de Queries Geradas
Sistema completo de validação de SQL gerado por NL2SQL

Valida:
1. Tabela detectada vs esperada
2. Campos válidos (apenas de tables_config.json)
3. Sintaxe SQL
4. Conversões de tipo necessárias
5. Formato JSON da function_call
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
import os

try:
    import sqlparse
    _HAS_SQLPARSE = True
except ImportError:
    _HAS_SQLPARSE = False


@dataclass
class ValidationResult:
    """Resultado de validação"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class SQLValidatorv2:
    """Validação 360° de SQL gerado por NL2SQL"""
    
    def __init__(self, tables_config_path: str = "tables_config.json"):
        self.config_path = tables_config_path
        self.config = self._load_config()
        self.table_field_map = self._build_field_map()
        
        if _HAS_SQLPARSE:
            print("[SQLValidator] sqlparse disponível ✅")
        else:
            print("[SQLValidator] Aviso: sqlparse não disponível, validações limitadas")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega arquivo de configuração"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config não encontrada: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _build_field_map(self) -> Dict[str, List[str]]:
        """Constrói mapa de campos válidos por tabela"""
        field_map = {}
        
        for table_name, table_config in self.config.items():
            if 'metadata' not in table_config:
                continue
            
            fields = table_config.get('fields', {})
            valid_fields = []
            
            # Adicionar todos os campos de todas as categorias
            for category in ['temporal_fields', 'dimension_fields', 'metric_fields', 'filter_fields']:
                for field_info in fields.get(category, []):
                    if isinstance(field_info, dict):
                        valid_fields.append(field_info.get('name', '').upper())
            
            # Adicionar também aliases comuns
            valid_fields.extend(['ID', 'SUM', 'COUNT', 'AVG', 'MAX', 'MIN', 'UPPER', 'LOWER'])
            
            field_map[table_name] = list(set(valid_fields))
        
        return field_map
    
    def validate_sql(
        self,
        sql: str,
        expected_table: str,
        debug: bool = False
    ) -> ValidationResult:
        """
        Valida SQL gerado
        
        Retorna ValidationResult com is_valid, errors, warnings e details
        """
        result = ValidationResult(is_valid=True)
        
        if debug:
            print(f"\n🔍 Validando SQL...")
            print(f"   Tabela esperada: {expected_table}")
        
        # [1] Validação básica
        if not sql or not isinstance(sql, str):
            result.is_valid = False
            result.errors.append("SQL vazio ou não é string")
            return result
        
        # [2] Detectar tabela usada
        detected_table, confidence = self.detect_table_from_sql(sql)
        result.details['detected_table'] = detected_table
        result.details['table_confidence'] = confidence
        
        # [3] Validar tabela
        table_validation = self._validate_table(detected_table, expected_table)
        if not table_validation['valid']:
            result.is_valid = False
            result.errors.append(table_validation['message'])
        result.details['table_validation'] = table_validation
        
        if debug:
            print(f"   Detectada: {detected_table} (confiança: {confidence:.1%})")
        
        # [4] Validar sintaxe SQL
        if _HAS_SQLPARSE:
            syntax_issues = self._validate_sql_syntax(sql)
            if syntax_issues:
                result.warnings.extend(syntax_issues)
                if debug:
                    print(f"   ⚠️  Avisos de sintaxe: {len(syntax_issues)}")
        
        # [5] Validar campos
        if detected_table in self.table_field_map:
            field_validation = self._validate_fields(sql, detected_table)
            if not field_validation['valid']:
                result.is_valid = False
                result.errors.extend(field_validation['messages'])
            result.details['field_validation'] = field_validation
            
            if debug:
                if field_validation['valid']:
                    print(f"   ✅ Campos válidos")
                else:
                    print(f"   ❌ Campos inválidos: {field_validation['messages']}")
        
        # [6] Validar conversões de tipo
        conversion_validation = self._validate_conversions(sql, detected_table)
        if conversion_validation['missing_conversions']:
            result.warnings.extend([
                f"Possível conversão de tipo ausente: {field}" 
                for field in conversion_validation['missing_conversions'][:3]
            ])
        result.details['conversions'] = conversion_validation
        
        # [7] Validar JSON format (se houver)
        if '{' in sql or '[' in sql:
            # Pode ser embutido em função
            pass
        
        return result
    
    def validate_function_call(
        self,
        function_call: Dict[str, Any],
        expected_table: str,
        debug: bool = False
    ) -> ValidationResult:
        """Valida estrutura de function_call JSON"""
        
        result = ValidationResult(is_valid=True)
        
        required_fields = ['cte', 'select', 'from_table', 'order_by']
        
        # [1] Verificar campos obrigatórios
        missing = [f for f in required_fields if f not in function_call]
        if missing:
            result.is_valid = False
            result.errors.append(f"Campos obrigatórios faltando: {missing}")
        
        # [2] Validar tipos
        type_errors = []
        if 'select' in function_call and not isinstance(function_call['select'], list):
            type_errors.append("'select' deve ser lista")
        if 'cte' in function_call and not isinstance(function_call['cte'], str):
            type_errors.append("'cte' deve ser string")
        if 'order_by' in function_call and not isinstance(function_call['order_by'], list):
            type_errors.append("'order_by' deve ser lista")
        
        if type_errors:
            result.is_valid = False
            result.errors.extend(type_errors)
        
        # [3] Construir SQL a partir de function_call e validar
        if result.is_valid:
            sql = self._build_sql_from_function_call(function_call)
            sql_validation = self.validate_sql(sql, expected_table, debug=debug)
            
            result.is_valid = sql_validation.is_valid
            result.errors.extend(sql_validation.errors)
            result.warnings.extend(sql_validation.warnings)
            result.details = sql_validation.details
        
        return result
    
    def detect_table_from_sql(self, sql: str) -> Tuple[Optional[str], float]:
        """
        Detecta qual tabela é usada na SQL
        
        Retorna (table_name, confidence_score)
        """
        sql_upper = sql.upper()
        
        best_match = None
        best_score = 0
        
        # Tentar detectar por FROM ou JOIN
        for table_name in self.config.keys():
            if 'metadata' not in self.config[table_name]:
                continue
            
            bigquery_table = self.config[table_name]['metadata'].get('bigquery_table', '')
            
            # Padrões de detecção
            patterns = [
                f"FROM.*{table_name}",
                f"FROM.*{bigquery_table}",
                f"JOIN.*{table_name}",
                f"JOIN.*{bigquery_table}",
                f"`{bigquery_table}`",
                f"\"{table_name}\"",
                f"'{table_name}'",
                table_name,  # Match simples
            ]
            
            score = 0
            for pattern in patterns:
                if re.search(pattern, sql_upper, re.IGNORECASE):
                    # Aumentar score por match mais específico
                    if 'FROM' in pattern:
                        score = 0.95
                    elif 'JOIN' in pattern:
                        score = 0.80
                    elif '`' in pattern:
                        score = 0.90
                    else:
                        score = 0.70
                    break
            
            if score > best_score:
                best_score = score
                best_match = table_name
        
        return best_match, best_score
    
    def _validate_table(
        self,
        detected: Optional[str],
        expected: str
    ) -> Dict[str, Any]:
        """Valida se tabela detectada bate com esperada"""
        
        if detected == expected:
            return {
                'valid': True,
                'message': f'Tabela correta: {detected}',
                'match_type': 'exact'
            }
        
        if detected is None:
            return {
                'valid': False,
                'message': f'Nenhuma tabela detectada (esperada: {expected})',
                'match_type': 'none'
            }
        
        return {
            'valid': False,
            'message': f'Tabela incorreta: detectada {detected}, esperada {expected}',
            'match_type': 'mismatch'
        }
    
    def _validate_fields(self, sql: str, table_name: str) -> Dict[str, Any]:
        """Valida se apenas campos válidos são usados"""
        
        if table_name not in self.table_field_map:
            return {'valid': True, 'messages': []}
        
        valid_fields = set(self.table_field_map[table_name])
        
        # Extrair campos usados (padrão: UPPERCASE palavras após SELECT, FROM, WHERE, etc)
        # Simplificado: procurar por field_name (sem spaces)
        pattern = r'\b([A-Za-z_][A-Za-z0-9_]*)\b'
        found_fields = set(re.findall(pattern, sql))
        
        # Filtrar palavras-chave SQL
        sql_keywords = {
            'SELECT', 'FROM', 'WHERE', 'ORDER', 'BY', 'GROUP', 'HAVING',
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'WITH', 'AS',
            'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'SUM', 'COUNT', 'AVG',
            'MAX', 'MIN', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
            'EXTRACT', 'CAST', 'SAFE_CAST', 'DATE', 'DATETIME', 'TIMESTAMP',
            'UPPER', 'LOWER', 'ROUND', 'ROW_NUMBER', 'OVER', 'PARTITION',
            'NULLIF', 'COALESCE', 'IF', 'NULL', 'TRUE', 'FALSE', 'ASC', 'DESC',
            'LIMIT', 'OFFSET', 'DISTINCT', 'UNION', 'ALL'
        }
        
        # Campos não identificados
        unknown_fields = found_fields - valid_fields - sql_keywords
        
        # Remover números e valores literal
        unknown_fields = {f for f in unknown_fields if not f.isdigit() and f not in ['_1', '_2', '_3']}
        
        messages = []
        if unknown_fields:
            return {
                'valid': False,
                'messages': [f"Campos desconhecidos: {', '.join(list(unknown_fields)[:5])}"],
                'unknown_fields': list(unknown_fields)[:10]
            }
        
        return {'valid': True, 'messages': []}
    
    def _validate_sql_syntax(self, sql: str) -> List[str]:
        """Valida sintaxe SQL com sqlparse"""
        
        warnings = []
        
        try:
            parsed = sqlparse.parse(sql)
            
            # Verificações básicas
            if not parsed:
                warnings.append("SQL não pôde ser parseado")
            
            # Verificar balanceamento de parênteses
            open_parens = sql.count('(')
            close_parens = sql.count(')')
            if open_parens != close_parens:
                warnings.append(f"Parênteses desbalanceados: {open_parens} abertura vs {close_parens} fechamento")
            
            # Verificar balanceamento de aspas
            single_quotes = sql.count("'")
            if single_quotes % 2 != 0:
                warnings.append("Aspas simples desbalanceadas")
            
            double_quotes = sql.count('"')
            if double_quotes % 2 != 0:
                warnings.append("Aspas duplas desbalanceadas")
            
        except Exception as e:
            warnings.append(f"Erro ao parsear SQL: {str(e)[:100]}")
        
        return warnings
    
    def _validate_conversions(self, sql: str, table_name: str) -> Dict[str, Any]:
        """Valida se conversões de tipo necessárias estão presentes"""
        
        missing_conversions = []
        
        # Campos que precisam conversão
        if table_name in self.config:
            table_config = self.config[table_name]
            fields = table_config.get('fields', {})
            
            # Verificar campos tipo STRING que precisam SAFE_CAST
            for field_info in fields.get('temporal_fields', []):
                if field_info.get('type') == 'STRING':
                    field_name = field_info.get('name', '')
                    # Se usa a data mas não em SAFE_CAST
                    if field_name in sql.upper() and f'SAFE_CAST({field_name}' not in sql.upper():
                        missing_conversions.append(field_name)
            
            for field_info in fields.get('metric_fields', []):
                if field_info.get('type') == 'STRING' and field_info.get('conversion'):
                    field_name = field_info.get('name', '')
                    if field_name in sql.upper() and 'SAFE_CAST' not in sql.upper():
                        missing_conversions.append(field_name)
        
        return {
            'has_safe_cast': 'SAFE_CAST' in sql.upper(),
            'missing_conversions': list(set(missing_conversions))[:5]
        }
    
    def _build_sql_from_function_call(self, func_call: Dict) -> str:
        """Reconstrói SQL a partir de function_call JSON"""
        
        try:
            cte = func_call.get('cte', '')
            select_list = func_call.get('select', [])
            from_table = func_call.get('from_table', '')
            where = func_call.get('where', '')
            order_by = func_call.get('order_by', [])
            limit = func_call.get('limit', '')
            
            select_clause = ", ".join(select_list) if isinstance(select_list, list) else str(select_list)
            order_clause = ", ".join(order_by) if isinstance(order_by, list) else str(order_by)
            
            sql = f"{cte}\nSELECT {select_clause}\nFROM {from_table}"
            
            if where:
                sql += f"\nWHERE {where}"
            
            if order_clause:
                sql += f"\nORDER BY {order_clause}"
            
            if limit:
                sql += f"\nLIMIT {limit}"
            
            return sql
        
        except Exception as e:
            return ""
    
    def is_query_safe(self, validation_result: ValidationResult) -> Tuple[bool, str]:
        """
        Determina se query é segura para executar
        
        Retorna (é_seguro, motivo)
        """
        
        if validation_result.errors:
            return False, f"Erros encontrados: {'; '.join(validation_result.errors[:2])}"
        
        # Warnings não bloqueiam execução
        if validation_result.warnings:
            return True, f"Avisos: {'; '.join(validation_result.warnings[:2])}"
        
        return True, "Query validada ✅"


if __name__ == "__main__":
    # Teste
    validator = SQLValidatorv2()
    
    # Teste 1: SQL correto
    sql_1 = """
    WITH cte_agregacao AS (
        SELECT nome_Vend, SUM(QTE) AS total_veiculos
        FROM glinhares.delivery.drvy_VeiculosVendas
        WHERE EXTRACT(YEAR FROM dta_venda) = 2024
        GROUP BY nome_Vend
    )
    SELECT nome_Vend, total_veiculos
    FROM cte_agregacao
    ORDER BY total_veiculos DESC
    """
    
    result = validator.validate_sql(sql_1, "drvy_VeiculosVendas", debug=True)
    print(f"\nResultado: {result.is_valid}")
    print(f"Erros: {result.errors}")
    print(f"Avisos: {result.warnings}")
