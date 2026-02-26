#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              TEST BACKEND FLOW - Teste direto sem Streamlit UI           ║
║                                                                           ║
║  Simula o fluxo completo:                                                ║
║  1. RAG (business_metadata + sql_patterns)                               ║
║  2. Gemini (NL → Parâmetros SQL)                                         ║
║  3. Build Query (Parâmetros → SQL)                                       ║
║  4. Execute (SQL → Resultados BigQuery)                                  ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import json
import sys
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path

# Adicionar raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports do projeto
from llm_handlers.gemini_handler import initialize_model, refine_with_gemini_rag
from rag_system.business_metadata_rag import BusinessMetadataRAGV2
from rag_system.sql_pattern_rag import SQLPatternRAG
from database.query_builder import build_query, execute_query
from database.validator import QueryValidator


class TestResultsManager:
    """Gerencia o diretório e arquivos de resultados dos testes"""
    
    def __init__(self):
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Criar subdiretórios
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.test_session_dir = self.results_dir / f"session_{self.timestamp}"
        self.test_session_dir.mkdir(exist_ok=True)
        
        # Subdiretórios específicos
        (self.test_session_dir / "sql_queries").mkdir(exist_ok=True)
        (self.test_session_dir / "results").mkdir(exist_ok=True)
        (self.test_session_dir / "errors").mkdir(exist_ok=True)
        (self.test_session_dir / "metrics").mkdir(exist_ok=True)
    
    def save_sql_query(self, test_id: int, question: str, sql: str, table: str):
        """Salva a SQL gerada para um teste"""
        filename = self.test_session_dir / "sql_queries" / f"test_{test_id:02d}.sql"
        content = f"""-- Teste #{test_id}
-- Pergunta: {question}
-- Tabela esperada: {table}
-- Data: {datetime.now().isoformat()}

{sql}
"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
    
    def save_result_data(self, test_id: int, result_data: Any):
        """Salva os dados de resultado brutos"""
        filename = self.test_session_dir / "results" / f"test_{test_id:02d}_result.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, default=str)
    
    def save_error(self, test_id: int, error: str, stacktrace: str = ""):
        """Salva informações de erro"""
        filename = self.test_session_dir / "errors" / f"test_{test_id:02d}_error.txt"
        content = f"""Teste: #{test_id}
Data: {datetime.now().isoformat()}

ERRO:
{error}

STACK TRACE:
{stacktrace}
"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)


class BackendFlowTester:
    """Tester para validar o fluxo completo sem UI"""
    
    def __init__(self, user_id: str = "backend_test", verbose: bool = False):
        self.user_id = user_id
        self.verbose = verbose
        self.results = []
        
        # Gerenciador de resultados
        self.results_manager = TestResultsManager()
        
        # Inicializa componentes
        print("🔧 Inicializando componentes...")
        self.rag_business = BusinessMetadataRAGV2()
        self.rag_patterns = SQLPatternRAG()
        self.gemini_model = initialize_model()
        self.query_validator = QueryValidator(max_retries=2)
        print("✅ Componentes inicializados!\n")
    
    def log_step(self, step: str, message: str, **context):
        """Log estruturado"""
        if self.verbose:
            print(f"  [{step}] {message}")
            if context:
                for k, v in context.items():
                    print(f"      {k}: {v}")
    
    def test_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Testa uma pergunta através do fluxo completo com validação de tabela
        
        Retorna: Dict com status, SQL, resultado, timing, validação de tabela, etc
        """
        question = question_data["question"]
        expected_table = question_data["expected_table"]
        test_id = question_data["test_number"]
        
        print(f"\n{'='*80}")
        print(f"  🧪 TESTE #{test_id}: {question}")
        print(f"  📍 Tabela esperada: {expected_table}")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        result = {
            "test_id": test_id,
            "question": question,
            "expected_table": expected_table,
            "detected_table": None,
            "table_validation": "PENDING",
            "timestamp": datetime.now().isoformat(),
            "status": "UNKNOWN",
            "stages": {},
            "generated_sql": None,
            "query_result": None,
            "error": None,
        }
        
        try:
            # ESTÁGIO 1: RAG (Business Metadata + SQL Patterns)
            print("📚 [ESTÁGIO 1] RAG - Recuperando contexto...")
            stage_start = time.time()
            
            # Recuperar metadados de negócio
            business_context = self._get_business_context(question)
            self.log_step("RAG", "Contexto de negócio recuperado")
            
            # Recuperar padrões SQL relevantes
            sql_patterns_context = self._get_sql_patterns_context()
            self.log_step("RAG", "Padrões SQL recuperados")
            
            stage_duration = time.time() - stage_start
            result["stages"]["rag"] = {
                "status": "OK",
                "duration_ms": int(stage_duration * 1000),
                "business_context_length": len(business_context),
                "patterns_count": len(sql_patterns_context.split("\n"))
            }
            print(f"   ✅ RAG concluído em {stage_duration:.2f}s\n")
            
            # ESTÁGIO 2: Gemini - Gerar parâmetros SQL
            print("🤖 [ESTÁGIO 2] Gemini - Gerando parâmetros SQL...")
            stage_start = time.time()
            
            function_params = self._call_gemini(
                question=question,
                business_context=business_context,
                sql_patterns_context=sql_patterns_context
            )
            
            if not function_params:
                raise ValueError("Gemini não retornou parâmetros válidos")
            
            self.log_step("Gemini", "Parâmetros gerados", params=str(function_params)[:100])
            
            stage_duration = time.time() - stage_start
            result["stages"]["gemini"] = {
                "status": "OK",
                "duration_ms": int(stage_duration * 1000),
                "params_keys": list(function_params.keys())
            }
            print(f"   ✅ Gemini concluído em {stage_duration:.2f}s\n")
            
            # ESTÁGIO 3: Build Query - Montar SQL final
            print("🔨 [ESTÁGIO 3] Build Query - Montando SQL...")
            stage_start = time.time()
            
            sql_query = build_query(function_params)
            
            if not sql_query:
                raise ValueError("Falha ao montar a query")
            
            result["generated_sql"] = sql_query
            
            # VALIDAÇÃO: Detectar qual tabela foi usada
            detected_table = self._detect_table_from_sql(sql_query)
            result["detected_table"] = detected_table
            
            # 💾 Salvar SQL gerada
            self.results_manager.save_sql_query(test_id, question, sql_query, expected_table)
            
            # Validar se usou a tabela esperada
            if detected_table == expected_table:
                result["table_validation"] = "PASSED ✅"
                print(f"   ✅ Tabela correta detectada: {detected_table}")
            else:
                result["table_validation"] = f"FAILED ❌ (usou {detected_table} ao invés de {expected_table})"
                print(f"   ❌ Tabela ERRADA detectada!")
                print(f"      Esperado: {expected_table}")
                print(f"      Detectado: {detected_table}")
            
            self.log_step("BuildQuery", "SQL gerado", sql_length=len(sql_query), table=detected_table)
            
            stage_duration = time.time() - stage_start
            result["stages"]["build_query"] = {
                "status": "OK",
                "duration_ms": int(stage_duration * 1000),
                "sql_length": len(sql_query),
                "table_validation": result["table_validation"]
            }
            print(f"   ✅ Build Query concluído em {stage_duration:.2f}s\n")
            
            # ESTÁGIO 4: Execute - Executar no BigQuery
            print("🚀 [ESTÁGIO 4] Execute - Executando SQL...")
            stage_start = time.time()
            
            # Executar query diretamente (sem retry complexo para economizar quota)
            query_result = execute_query(
                query=sql_query,
                user_question=question,
                gemini_model=self.gemini_model,
                validate=False  # Sem validação para economizar quota de Gemini
            )
            
            # Verificar se há erro
            if isinstance(query_result, dict) and "error" in query_result:
                error_msg = query_result["error"]
                print(f"   ❌ Erro SQL: {error_msg}")
                
                # RETRY INTELIGENTE: Se RAG acertou a tabela, tenta refinar com Gemini
                if detected_table == expected_table:
                    print(f"   🔄 RAG acertou a tabela! Tentando refinar SQL com Gemini...")
                    
                    try:
                        from llm_handlers.gemini_handler import refine_sql_with_error
                        
                        refined_result, refined_tech_details = refine_sql_with_error(
                            model=self.gemini_model,
                            user_question=question,
                            error_message=error_msg,
                            previous_sql=sql_query,
                            table_name=detected_table,
                            best_table_score=None
                        )
                        
                        if refined_result and isinstance(refined_result, dict):
                            print(f"   ✅ Gemini retornou SQL refinada, tentando executar...")
                            
                            # Constrói e executa SQL refinada
                            refined_sql = build_query(refined_result)
                            query_result_retry = execute_query(
                                query=refined_sql,
                                user_question=question,
                                gemini_model=self.gemini_model,
                                validate=False
                            )
                            
                            if not (isinstance(query_result_retry, dict) and "error" in query_result_retry):
                                print(f"   ✅ SQL refinada PASSOU!")
                                query_result = query_result_retry
                                sql_query = refined_sql
                                result["stages"]["execute"]["retry_successful"] = True
                            else:
                                print(f"   ❌ SQL refinada também falhou: {query_result_retry.get('error', 'Desconhecido')}")
                        else:
                            print(f"   ⚠️  Gemini não retornou SQL válida para refinamento")
                    except Exception as retry_e:
                        print(f"   ⚠️  Erro ao refinar: {retry_e}")
                
                # Se ainda há erro, falha
                if isinstance(query_result, dict) and "error" in query_result:
                    raise Exception(query_result["error"])
            
            result["query_result"] = query_result
            result["status"] = "PASSED"
            
            self.log_step("Execute", f"Query executada com sucesso", rows=len(query_result) if isinstance(query_result, list) else 0)
            
            stage_duration = time.time() - stage_start
            result["stages"]["execute"] = {
                "status": "OK",
                "duration_ms": int(stage_duration * 1000),
                "rows_returned": len(query_result) if isinstance(query_result, list) else 0
            }
            print(f"   ✅ Execute concluído em {stage_duration:.2f}s\n")
            
            # Resultado final
            total_duration = time.time() - start_time
            result["total_duration_ms"] = int(total_duration * 1000)
            
            print(f"✅ TESTE #{test_id} PASSOU em {total_duration:.2f}s")
            print(f"   Resultado: {len(query_result) if isinstance(query_result, list) else 0} linhas retornadas\n")
            
            # Mostrar primeira linha como amostra
            if isinstance(query_result, list) and query_result:
                print(f"   📊 Amostra de dados:")
                print(f"      {json.dumps(query_result[0], indent=6, default=str)}\n")
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
            total_duration = time.time() - start_time
            result["total_duration_ms"] = int(total_duration * 1000)
            
            print(f"❌ TESTE #{test_id} FALHOU em {total_duration:.2f}s")
            print(f"   Erro: {e}\n")
            
            # Log estruturado do erro
            print(f"   Erro interno: {type(e).__name__}")
            
            # 💾 Salvar erro
            import traceback
            self.results_manager.save_error(test_id, str(e), traceback.format_exc())
        
        self.results.append(result)
        return result
    
    def _get_business_context(self, question: str = "") -> str:
        """Recupera contexto de negócio via RAG v3 (prioriza tabela mais relevante)"""
        try:
            from config.settings import TABLES_CONFIG
            from rag_system.business_metadata_rag_v3 import BusinessMetadataRAGv3
            
            # USAR RAG v3 para identificar melhores tabelas
            try:
                rag_v3 = BusinessMetadataRAGv3()
                top_tables = rag_v3.get_top_3_tables(question, debug=False)
                print(f"📊 [RAG v3] Top 3 tabelas: {top_tables}")
            except Exception as e:
                print(f"⚠️  [RAG v3] Erro: {e}, usando todas as tabelas")
                top_tables = list(TABLES_CONFIG.keys())
            
            # Priorizar tabelas identificadas por RAG v3
            context_parts = []
            
            # Primeiro: tabelas top 3 do RAG v3
            for table_name in top_tables:
                if table_name in TABLES_CONFIG:
                    config = TABLES_CONFIG[table_name]
                    metadata = config.get('metadata', {})
                    description = metadata.get('description', '')
                    domain = metadata.get('domain', '')
                    bigquery_table = metadata.get('bigquery_table', '')
                    
                    # Extrair TODOS os campos disponíveis
                    all_fields = []
                    for field_type in ['temporal_fields', 'dimension_fields', 'metric_fields', 'filter_fields']:
                        fields = config.get('fields', {}).get(field_type, [])
                        for f in fields:
                            if isinstance(f, dict) and 'name' in f:
                                all_fields.append(f['name'])
                    
                    fields_desc = self._format_fields_description(config.get('fields', {}))
                    rules_desc = self._format_rules_description(config.get('business_rules', {}))
                    
                    context_parts.append(f"""
🎯 TABELA RECOMENDADA: {table_name}
   ⚠️  USE SEMPRE ESTE NOME COMPLETO NA QUERY: `{bigquery_table}`
   📋 CAMPOS DISPONÍVEIS NESTA TABELA: {', '.join(all_fields[:30])}
   
Descrição: {description}
Domínio: {domain}

CAMPOS COM DETALHES:
{fields_desc}

REGRAS DE NEGÓCIO:
{rules_desc}
                    """)
            
            # Segundo: outras tabelas (context apenas)
            for table_name, config in TABLES_CONFIG.items():
                if table_name not in top_tables:
                    metadata = config.get('metadata', {})
                    description = metadata.get('description', '')
                    domain = metadata.get('domain', '')
                    
                    context_parts.append(f"""
📋 TABELA ALTERNATIVA: {table_name}
Descrição: {description}
Domínio: {domain}
                    """)
            
            return "\n".join(context_parts)
        
        except Exception as e:
            print(f"⚠️  Erro ao recuperar contexto de negócio: {e}")
            return ""
    
    def _get_sql_patterns_context(self) -> str:
        """Recupera padrões SQL disponíveis"""
        try:
            import json
            import os
            
            # Procurar sql_patterns.json em várias localizações
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "..", "config", "sql_patterns.json"),
                os.path.join(os.path.dirname(__file__), "..", "sql_patterns.json"),
                "sql_patterns.json",
            ]
            
            patterns_file = None
            for path in possible_paths:
                if os.path.exists(path):
                    patterns_file = path
                    break
            
            if not patterns_file:
                print("⚠️  sql_patterns.json não encontrado")
                return ""
            
            with open(patterns_file, "r", encoding="utf-8") as f:
                patterns = json.load(f)
            
            patterns_list = patterns.get("sql_patterns", {})
            context_parts = []
            
            for pattern_name, pattern_def in patterns_list.items():
                description = pattern_def.get("description", "")
                template = pattern_def.get("sql_template", "")
                
                context_parts.append(f"""
PADRÃO: {pattern_name}
Descrição: {description}
Exemplo:
{template[:200]}...
                """)
            
            return "\n".join(context_parts)
        
        except Exception as e:
            print(f"⚠️  Erro ao recuperar padrões SQL: {e}")
            return ""
    
    def _format_fields_description(self, fields_dict: Dict) -> str:
        """Formata descrição dos campos"""
        parts = []
        for category, field_list in fields_dict.items():
            if isinstance(field_list, list):
                parts.append(f"\n{category.upper()}:")
                for field in field_list:
                    if isinstance(field, dict):
                        name = field.get("name", "?")
                        field_type = field.get("type", "?")
                        description = field.get("description", "")
                        parts.append(f"  - {name} ({field_type}): {description}")
        
        return "\n".join(parts)
    
    def _format_rules_description(self, rules_dict: Dict) -> str:
        """Formata descrição das regras"""
        parts = []
        for rule_type, rule_list in rules_dict.items():
            if isinstance(rule_list, list):
                parts.append(f"\n{rule_type.upper()}:")
                for rule in rule_list[:3]:  # Limitar a 3 regras por tipo
                    if isinstance(rule, dict):
                        rule_text = rule.get("rule", "")
                        context = rule.get("context", "")
                        parts.append(f"  • {rule_text} ({context})")
        
        return "\n".join(parts)
    
    def _detect_table_from_sql(self, sql_query: str) -> str:
        """
        Detecta qual tabela foi usada na SQL
        Procura por referências explícitas à tabela no FROM/JOIN
        """
        import re
        
        sql_upper = sql_query.upper()
        
        # Tabelas disponíveis com seus possíveis nomes na SQL
        table_patterns = {
            "drvy_VeiculosVendas": [
                r"glinhares\.delivery\.drvy_VeiculosVendas",
                r"drvy_VeiculosVendas"
            ],
            "dvry_ihs_cotas_ativas": [
                r"glinhares\.delivery\.dvry_ihs_cotas_ativas",
                r"dvry_ihs_cotas_ativas"
            ],
            "dvry_ihs_qualidade_vendas_historico": [
                r"glinhares\.delivery\.dvry_ihs_qualidade_vendas_historico",
                r"dvry_ihs_qualidade_vendas_historico"
            ]
        }
        
        # Procurar pela primeira tabela encontrada
        for table_name, patterns in table_patterns.items():
            for pattern in patterns:
                if re.search(pattern, sql_upper, re.IGNORECASE):
                    return table_name
        
        return "UNKNOWN"
    
    def _call_gemini(self, question: str, business_context: str, sql_patterns_context: str) -> Dict:
        """Chama Gemini para gerar parâmetros SQL"""
        import json
        import re
        
        try:
            # Chamar refine_with_gemini_rag que retorna (function_call, tech_details)
            result = refine_with_gemini_rag(
                model=self.gemini_model,
                user_question=question,
                user_id=self.user_id
            )
            
            # Desempacotar o resultado
            if isinstance(result, tuple):
                function_call, tech_details = result
                
                # Se for string JSON, fazer parse
                if isinstance(function_call, str):
                    # Remover markdown code blocks (```json ... ```)
                    function_call = re.sub(r'```json\n?', '', function_call)
                    function_call = re.sub(r'```\n?', '', function_call)
                    params = json.loads(function_call)
                elif hasattr(function_call, '__dict__'):
                    params = function_call.__dict__
                else:
                    params = function_call
            else:
                params = result
            
            # Se ainda for string, é erro
            if isinstance(params, str):
                # Tenta fazer parse mesmo assim
                params_str = re.sub(r'```json\n?', '', params)
                params_str = re.sub(r'```\n?', '', params_str)
                try:
                    params = json.loads(params_str)
                except:
                    raise ValueError(f"Não conseguiu parsear resposta: {params}")
            
            return params
        
        except Exception as e:
            print(f"⚠️  Erro ao chamar Gemini: {e}")
            raise
    
    def print_summary(self):
        """Imprime sumário dos testes"""
        print(f"\n{'='*80}")
        print(f"  📊 SUMÁRIO DOS TESTES")
        print(f"{'='*80}\n")
        
        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        total = len(self.results)
        
        print(f"  ✅ Passou: {passed}/{total}")
        print(f"  ❌ Falhou: {failed}/{total}")
        
        if total > 0:
            accuracy = (passed / total) * 100
            print(f"  📈 Acurácia: {accuracy:.1f}%\n")
        
        # Validação de tabela
        table_correct = len([r for r in self.results if "PASSED" in str(r["table_validation"])])
        print(f"  🎯 Tabelas identificadas corretamente: {table_correct}/{total}")
        
        # Listar testes com tabela errada
        wrong_table_tests = [r for r in self.results if "FAILED" in str(r["table_validation"])]
        if wrong_table_tests:
            print(f"\n  ⚠️  Testes com tabela errada:")
            for test in wrong_table_tests:
                print(f"      Teste #{test['test_id']}: esperado {test['expected_table']}, detectado {test['detected_table']}")
        
        # Erros por tipo
        errors_by_type = {}
        for result in self.results:
            if result["error"]:
                error_type = type(result["error"]).__name__ if isinstance(result["error"], Exception) else "Unknown"
                errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
        
        if errors_by_type:
            print(f"\n  🔴 Erros por tipo:")
            for error_type, count in errors_by_type.items():
                print(f"      - {error_type}: {count}")
        
        # Tempo total
        total_time = sum(r["total_duration_ms"] for r in self.results) / 1000
        avg_time = total_time / total if total > 0 else 0
        
        print(f"\n  ⏱️  Tempo total: {total_time:.1f}s")
        print(f"  ⏱️  Tempo médio: {avg_time:.1f}s\n")
        
        print(f"{'='*80}\n")
    
    def save_results(self):
        """Salva resultados em JSON, LOG, HTML e CSV no diretório de sessão"""
        
        # Calcular métricas
        total_tests = len(self.results)
        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        table_correct = len([r for r in self.results if "PASSED" in str(r["table_validation"])])
        
        accuracy = (passed / total_tests * 100) if total_tests > 0 else 0
        table_accuracy = (table_correct / total_tests * 100) if total_tests > 0 else 0
        
        # ==================== ARQUIVO JSON ====================
        json_filename = self.results_manager.test_session_dir / "results.json"
        output_json = {
            "metadata": {
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "accuracy_percent": round(accuracy, 2),
                "table_validation_accuracy": round(table_accuracy, 2),
                "session_dir": str(self.results_manager.test_session_dir),
            },
            "results": self.results
        }
        
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(output_json, f, indent=2, default=str)
        
        print(f"✅ JSON salvo em: {json_filename}")
        
        # ==================== ARQUIVO TXT (LOG DETALHADO) ====================
        log_filename = self.results_manager.test_session_dir / "report.txt"
        log_lines = self._generate_detailed_report(total_tests, passed, failed, table_correct)
        
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
        
        print(f"✅ Relatório TXT salvo em: {log_filename}")
        
        # ==================== ARQUIVO CSV ====================
        csv_filename = self.results_manager.test_session_dir / "results.csv"
        csv_lines = self._generate_csv_report()
        
        with open(csv_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(csv_lines))
        
        print(f"✅ CSV salvo em: {csv_filename}")
        
        # ==================== ARQUIVO HTML ====================
        html_filename = self.results_manager.test_session_dir / "report.html"
        html_content = self._generate_html_report(total_tests, passed, failed, table_correct, accuracy, table_accuracy)
        
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"✅ Relatório HTML salvo em: {html_filename}")
        
        # ==================== ARQUIVO ÍNDICE ====================
        index_filename = self.results_manager.test_session_dir / "index.txt"
        index_lines = [
            "=" * 100,
            "ÍNDICE DE TESTES - SESSION " + self.results_manager.timestamp,
            "=" * 100,
            "",
            f"📊 Resultados Gerais:",
            f"  Total: {total_tests} testes",
            f"  Passou: {passed} ({accuracy:.1f}%)",
            f"  Falhou: {failed}",
            f"  Tabelas Corretas: {table_correct} ({table_accuracy:.1f}%)",
            "",
            f"📁 Arquivos Gerados:",
            f"  results.json  - Dados JSON completos (importável)",
            f"  results.csv   - Dados em CSV (para Excel/importação)",
            f"  report.txt    - Relatório textual detalhado",
            f"  report.html   - Relatório HTML interativo",
            f"  index.txt     - Este arquivo",
            "",
            f"📂 Subdiretórios:",
            f"  sql_queries/  - Queries SQL geradas para cada teste",
            f"  results/      - Dados de resultado de cada teste",
            f"  errors/       - Erros e stack traces detalhados",
            f"  metrics/      - Métricas e análises",
            "",
            "=" * 100,
        ]
        
        with open(index_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(index_lines))
        
        print(f"✅ Índice salvo em: {index_filename}")
        
        # ==================== SALVAR DADOS INDIVIDUAIS ====================
        for result in self.results:
            test_id = result["test_id"]
            self.results_manager.save_result_data(test_id, result)
        
        return self.results_manager.test_session_dir
    
    def _generate_detailed_report(self, total_tests, passed, failed, table_correct) -> List[str]:
        """Gera relatório detalhado em texto"""
        log_lines = []
        log_lines.append("=" * 100)
        log_lines.append(f"RELATÓRIO DETALHADO - TESTE BACKEND FLOW")
        log_lines.append(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_lines.append("=" * 100)
        log_lines.append("")
        
        # Sumário geral
        accuracy = (passed / total_tests * 100) if total_tests > 0 else 0
        table_accuracy = (table_correct / total_tests * 100) if total_tests > 0 else 0
        
        log_lines.append("📊 SUMÁRIO GERAL")
        log_lines.append("-" * 100)
        log_lines.append(f"Total de testes: {total_tests}")
        log_lines.append(f"Testes passou: {passed} ({accuracy:.1f}%)")
        log_lines.append(f"Testes falhou: {failed}")
        log_lines.append(f"Tabelas identificadas corretamente: {table_correct} ({table_accuracy:.1f}%)")
        log_lines.append("")
        
        # Tempo total
        total_time = sum(r["total_duration_ms"] for r in self.results) / 1000
        avg_time = total_time / total_tests if total_tests > 0 else 0
        log_lines.append(f"Tempo total: {total_time:.2f}s")
        log_lines.append(f"Tempo médio por teste: {avg_time:.2f}s")
        log_lines.append("")
        
        # Detalhes de cada teste
        log_lines.append("=" * 100)
        log_lines.append("📋 DETALHES DE CADA TESTE")
        log_lines.append("=" * 100)
        log_lines.append("")
        
        for result in self.results:
            test_id = result["test_id"]
            status = result["status"]
            question = result["question"]
            expected_table = result["expected_table"]
            detected_table = result["detected_table"]
            table_validation = result["table_validation"]
            error = result["error"]
            duration_ms = result["total_duration_ms"]
            
            status_icon = "✅" if status == "PASSED" else "❌"
            
            log_lines.append(f"[{status_icon}] TESTE #{test_id}: {status}")
            log_lines.append(f"    Pergunta: {question}")
            log_lines.append(f"    Tabela Esperada: {expected_table}")
            log_lines.append(f"    Tabela Detectada: {detected_table}")
            log_lines.append(f"    Validação de Tabela: {table_validation}")
            log_lines.append(f"    Duração: {duration_ms}ms")
            
            if error:
                log_lines.append(f"    ❌ Erro: {error}")
            
            stages = result.get("stages", {})
            if stages:
                log_lines.append(f"    Estágios:")
                for stage_name, stage_info in stages.items():
                    stage_status = stage_info.get("status", "?")
                    stage_duration = stage_info.get("duration_ms", 0)
                    log_lines.append(f"      - {stage_name}: {stage_status} ({stage_duration}ms)")
            
            sql = result.get("generated_sql")
            if sql:
                sql_preview = sql[:150] + "..." if len(sql) > 150 else sql
                log_lines.append(f"    SQL (preview): {sql_preview}")
            
            query_result = result.get("query_result")
            if query_result:
                row_count = len(query_result) if isinstance(query_result, list) else 0
                log_lines.append(f"    Resultado: {row_count} linhas retornadas")
                if row_count > 0 and isinstance(query_result, list):
                    first_row_preview = json.dumps(query_result[0], default=str)[:100]
                    log_lines.append(f"    Primeira linha: {first_row_preview}")
            
            log_lines.append("")
        
        # Análise de erros
        log_lines.append("=" * 100)
        log_lines.append("🔴 ANÁLISE DE ERROS")
        log_lines.append("=" * 100)
        log_lines.append("")
        
        errors_by_type = {}
        for result in self.results:
            if result["error"]:
                error_type = type(result["error"]).__name__ if isinstance(result["error"], Exception) else "Unknown"
                if error_type not in errors_by_type:
                    errors_by_type[error_type] = []
                errors_by_type[error_type].append({
                    "test_id": result["test_id"],
                    "error": result["error"]
                })
        
        if errors_by_type:
            for error_type, errors in errors_by_type.items():
                log_lines.append(f"Erro: {error_type} ({len(errors)} ocorrências)")
                for error_info in errors[:3]:
                    log_lines.append(f"  - Teste #{error_info['test_id']}: {error_info['error'][:80]}")
                if len(errors) > 3:
                    log_lines.append(f"  ... e mais {len(errors) - 3} ocorrências")
                log_lines.append("")
        else:
            log_lines.append("✅ Nenhum erro encontrado!")
            log_lines.append("")
        
        # Análise de tabelas
        log_lines.append("=" * 100)
        log_lines.append("🎯 ANÁLISE DE TABELAS")
        log_lines.append("=" * 100)
        log_lines.append("")
        
        table_stats = {}
        for result in self.results:
            expected_table = result["expected_table"]
            detected_table = result["detected_table"]
            table_validation = result["table_validation"]
            
            if expected_table not in table_stats:
                table_stats[expected_table] = {"total": 0, "correct": 0, "wrong": []}
            
            table_stats[expected_table]["total"] += 1
            if "PASSED" in str(table_validation):
                table_stats[expected_table]["correct"] += 1
            else:
                table_stats[expected_table]["wrong"].append({
                    "test_id": result["test_id"],
                    "detected": detected_table
                })
        
        for table_name, stats in table_stats.items():
            total = stats["total"]
            correct = stats["correct"]
            percent = (correct / total * 100) if total > 0 else 0
            
            log_lines.append(f"Tabela: {table_name}")
            log_lines.append(f"  Testes: {total}")
            log_lines.append(f"  Corretos: {correct} ({percent:.1f}%)")
            
            if stats["wrong"]:
                log_lines.append(f"  Incorretos:")
                for wrong in stats["wrong"]:
                    log_lines.append(f"    - Teste #{wrong['test_id']}: detectou {wrong['detected']}")
            
            log_lines.append("")
        
        log_lines.append("=" * 100)
        log_lines.append(f"Relatório gerado em: {datetime.now().isoformat()}")
        log_lines.append("=" * 100)
        
        return log_lines
    
    def _generate_csv_report(self) -> List[str]:
        """Gera relatório em CSV"""
        lines = []
        # Header
        lines.append("test_id,question,expected_table,detected_table,status,table_validation,duration_ms,error")
        
        # Dados
        for result in self.results:
            test_id = result["test_id"]
            question = result["question"].replace(",", ";")  # Escapar vírgulas
            expected_table = result["expected_table"]
            detected_table = result.get("detected_table", "UNKNOWN")
            status = result["status"]
            table_validation = str(result["table_validation"]).replace(",", ";")
            duration_ms = result["total_duration_ms"]
            error = result["error"] if result["error"] else ""
            error = str(error).replace(",", ";").replace("\n", " ")[:100]  # Limitar tamanho
            
            line = f'{test_id},"{question}",{expected_table},{detected_table},{status},"{table_validation}",{duration_ms},"{error}"'
            lines.append(line)
        
        return lines
    
    def _generate_html_report(self, total_tests, passed, failed, table_correct, accuracy, table_accuracy) -> str:
        """Gera relatório em HTML interativo"""
        html_parts = []
        
        html_parts.append("""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Testes - Backend Flow</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .metric-card h3 {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .metric-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .metric-card.success { border-left-color: #28a745; }
        .metric-card.error { border-left-color: #dc3545; }
        .metric-card.warning { border-left-color: #ffc107; }
        .metric-card.success .value { color: #28a745; }
        .metric-card.error .value { color: #dc3545; }
        .metric-card.warning .value { color: #ff9800; }
        
        .section {
            padding: 40px;
            border-bottom: 1px solid #eee;
        }
        .section h2 {
            color: #333;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .test-result {
            background: #f8f9fa;
            border-left: 4px solid #ddd;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
        }
        .test-result.passed {
            border-left-color: #28a745;
            background: #f0f8f5;
        }
        .test-result.failed {
            border-left-color: #dc3545;
            background: #fdf5f5;
        }
        .test-result h4 {
            color: #333;
            margin-bottom: 8px;
        }
        .test-result p {
            margin: 4px 0;
            font-size: 0.95em;
            color: #666;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            margin-right: 5px;
        }
        .badge.success { background: #d4edda; color: #155724; }
        .badge.danger { background: #f8d7da; color: #721c24; }
        .badge.info { background: #d1ecf1; color: #0c5460; }
        
        .code-block {
            background: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 12px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        table th {
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #ddd;
            color: #333;
            font-weight: bold;
        }
        table td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        table tr:hover {
            background: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Relatório de Testes Backend Flow</h1>
            <p>Validação completa do pipeline: RAG → Gemini → Build Query → Execute</p>
            <p style="font-size: 0.9em; margin-top: 10px;">""" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card success">
                <h3>✅ Testes Passados</h3>
                <div class="value">""" + str(passed) + f"""/{total_tests}</div>
                <p style="font-size: 0.9em; margin-top: 5px;">{accuracy:.1f}% de acurácia</p>
            </div>
            <div class="metric-card error">
                <h3>❌ Testes Falhados</h3>
                <div class="value">""" + str(failed) + """</div>
            </div>
            <div class="metric-card warning">
                <h3>🎯 Tabelas Corretas</h3>
                <div class="value">""" + str(table_correct) + f"""/{total_tests}</div>
                <p style="font-size: 0.9em; margin-top: 5px;">{table_accuracy:.1f}% acurácia RAG</p>
            </div>
            <div class="metric-card">
                <h3>⏱️ Tempo Total</h3>
                <div class="value">""" + f"{sum(r['total_duration_ms'] for r in self.results) / 1000:.1f}s" + """</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 Resultados Detalhados por Teste</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 50px;">ID</th>
                        <th>Pergunta</th>
                        <th>Tabela Esperada</th>
                        <th>Tabela Detectada</th>
                        <th>Status</th>
                        <th style="width: 100px;">Duração</th>
                    </tr>
                </thead>
                <tbody>
        """)
        
        for result in self.results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            status_class = "passed" if result["status"] == "PASSED" else "failed"
            table_match = "✅" if "PASSED" in str(result["table_validation"]) else "❌"
            
            html_parts.append(f"""
                    <tr>
                        <td>#{result["test_id"]}</td>
                        <td>{result["question"][:60]}</td>
                        <td>{result["expected_table"]}</td>
                        <td>{table_match} {result.get("detected_table", "UNKNOWN")}</td>
                        <td><span class="badge {status_class}">{status_icon} {result["status"]}</span></td>
                        <td>{result["total_duration_ms"]}ms</td>
                    </tr>
            """)
        
        html_parts.append("""
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>🎯 Validação de Tabelas</h2>
        """)
        
        # Análise de tabelas
        table_stats = {}
        for result in self.results:
            expected_table = result["expected_table"]
            if expected_table not in table_stats:
                table_stats[expected_table] = {"total": 0, "correct": 0}
            table_stats[expected_table]["total"] += 1
            if "PASSED" in str(result["table_validation"]):
                table_stats[expected_table]["correct"] += 1
        
        for table_name, stats in sorted(table_stats.items()):
            percent = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
            html_parts.append(f"""
            <div style="margin-bottom: 20px;">
                <h4>{table_name}</h4>
                <p>Acurácia: {stats["correct"]}/{stats["total"]} ({percent:.1f}%)</p>
                <div style="background: #e9ecef; height: 20px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #28a745; height: 100%; width: {percent}%; transition: width 0.3s;"></div>
                </div>
            </div>
            """)
        
        html_parts.append("""
        </div>
        
        <div class="footer">
            <p>Gerado automaticamente pelo sistema de teste backend flow</p>
            <p>""" + str(self.results_manager.test_session_dir) + """</p>
        </div>
    </div>
</body>
</html>
        """)
        
        return "".join(html_parts)


# PERGUNTAS DE TESTE DIRECIONADAS POR TABELA
# Cada pergunta indica claramente qual tabela deve ser usada
# O RAG deve identificar a tabela correta baseado na pergunta

TEST_QUESTIONS = [
    # ========================================
    # TABELA 1: drvy_VeiculosVendas (Vendas de Veículos)
    # ========================================
    {
        "question": "Qual o total de veículos vendidos por mês em 2024?",
        "expected_table": "drvy_VeiculosVendas",
        "keywords": ["vendidos", "veículos", "mês", "2024"],
        "test_number": 1
    },
    {
        "question": "Quantas unidades de carros foram vendidas em Fortaleza?",
        "expected_table": "drvy_VeiculosVendas",
        "keywords": ["carros", "Fortaleza", "vendidas"],
        "test_number": 2
    },
    {
        "question": "qual total de carros e motos vendidos em 2024 por uf?",
        "expected_table": "drvy_VeiculosVendas",
        "keywords": ["veiculo", "total", "venda"],
        "test_number": 3
    },
    {
        "question": "Top 5 vendedores por valor total de vendas de veículos",
        "expected_table": "drvy_VeiculosVendas",
        "keywords": ["vendedores", "valor", "vendas", "veículos"],
        "test_number": 4
    },
    
    # ========================================
    # TABELA 2: dvry_ihs_cotas_ativas (Contratos de Consórcio)
    # ========================================
    {
        "question": "Quantos contratos de consórcio ativos existem por estado?",
        "expected_table": "dvry_ihs_cotas_ativas",
        "keywords": ["contratos", "consórcio", "estado"],
        "test_number": 5
    },
    {
        "question": "Qual é o valor médio de quitação dos contratos ativos?",
        "expected_table": "dvry_ihs_cotas_ativas",
        "keywords": ["quitação", "contratos", "valor"],
        "test_number": 6
    },
    {
        "question": "Ranking de vendedores por número de cotas de consórcio ativas",
        "expected_table": "dvry_ihs_cotas_ativas",
        "keywords": ["vendedores", "cotas", "consórcio"],
        "test_number": 7
    },
    {
        "question": "Qual é o percentual médio amortizado dos contratos de consórcio?",
        "expected_table": "dvry_ihs_cotas_ativas",
        "keywords": ["amortizado", "contratos", "consórcio"],
        "test_number": 8
    },
    
    # ========================================
    # TABELA 3: dvry_ihs_qualidade_vendas_historico (Histórico de Vendas)
    # ========================================
    {
        "question": "Quais são os top 10 produtos mais vendidos?",
        "expected_table": "dvry_ihs_qualidade_vendas_historico",
        "keywords": ["produtos", "top 10", "vendidos", "ranking"],
        "test_number": 9
    },
    {
        "question": "Quantas propostas de consórcio foram vendidas em 2024?",
        "expected_table": "dvry_ihs_qualidade_vendas_historico",
        "keywords": ["propostas", "consórcio", "vendidas", "histórico"],
        "test_number": 10
    },
    {
        "question": "Qual é o vendedor com maior volume de propostas em 2024?",
        "expected_table": "dvry_ihs_qualidade_vendas_historico",
        "keywords": ["vendedor", "propostas", "histórico"],
        "test_number": 11
    },
    {
        "question": "Evolução de vendas de consórcio por origem do contrato em 2024",
        "expected_table": "dvry_ihs_qualidade_vendas_historico",
        "keywords": ["origem", "contrato", "histórico", "evolução"],
        "test_number": 12
    },
    {
        "question": "Top 5 planos de consórcio mais vendidos no histórico de vendas",
        "expected_table": "dvry_ihs_qualidade_vendas_historico",
        "keywords": ["planos", "consórcio", "histórico"],
        "test_number": 13
    },
]


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Testa fluxo backend com validação de RAG")
    parser.add_argument("--test-id", type=int, help="Rodar teste específico (1-13)")
    parser.add_argument("--verbose", action="store_true", help="Modo verbose")
    parser.add_argument("--user-id", default="backend_test", help="User ID para logging")
    
    args = parser.parse_args()
    
    # Inicializar tester
    tester = BackendFlowTester(user_id=args.user_id, verbose=args.verbose)
    
    # Rodar testes
    if args.test_id:
        # Teste específico
        matching_tests = [q for q in TEST_QUESTIONS if q["test_number"] == args.test_id]
        if matching_tests:
            question_data = matching_tests[0]
            tester.test_question(question_data)
        else:
            print(f"❌ Test ID deve estar entre 1 e {len(TEST_QUESTIONS)}")
            sys.exit(1)
    else:
        # Todos os testes
        for question_data in TEST_QUESTIONS:
            tester.test_question(question_data)
    
    # Mostrar sumário
    tester.print_summary()
    
    # Salvar resultados
    session_dir = tester.save_results()
    
    print(f"\n{'='*80}")
    print(f"📁 RESULTADOS SALVOS EM:")
    print(f"   {session_dir}")
    print(f"{'='*80}\n")
    
    print(f"📊 Arquivos gerados:")
    print(f"   ✅ results.json     - Dados completos em JSON")
    print(f"   ✅ results.csv      - Dados em CSV (importar em Excel)")
    print(f"   ✅ report.txt       - Relatório detalhado em texto")
    print(f"   ✅ report.html      - Relatório interativo em HTML")
    print(f"   ✅ index.txt        - Índice de arquivos")
    print(f"\n📂 Subdiretórios:")
    print(f"   📁 sql_queries/     - SQLs geradas para cada teste")
    print(f"   📁 results/         - Dados de resultado de cada teste")
    print(f"   📁 errors/          - Erros e stack traces detalhados")
    print(f"\n💡 Dicas:")
    print(f"   - Abra report.html em um navegador para visualizar o relatório interativo")
    print(f"   - Use results.json para importar dados programaticamente")
    print(f"   - Use results.csv para abrir em Excel ou Sheets")
    print(f"   - Verifique errors/ para investigar testes que falharam")
    print(f"   - Verifique sql_queries/ para revisar as SQLs geradas")
    print(f"\n")


if __name__ == "__main__":
    main()
