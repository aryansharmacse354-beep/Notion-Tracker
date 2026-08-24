"""Lightweight Python Localization (i18n) Engine for Notion Tracker.

Enables dynamic Notion-Native Typesetting and Dashboard UI translation
across English, Spanish, German, Japanese, Hindi, and French.
"""

from typing import Dict, Any, Optional
import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent / "data" / "system_config.json"

# Multilingual Translation Dictionary
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # Notion Typesetting Keys
        "ai_decision_engine": "🧠 AI Pre-Audit & Decision Engine",
        "risk_evaluation_banner": "{emoji} {risk_level} RISK PRE-AUDIT EVALUATION (Confidence: {confidence}%)",
        "task_specifications": "📋 Task Specifications & Payload",
        "category_label": "Category",
        "requested_priority": "Requested Priority",
        "task_summary": "Task Summary",
        "cot_reasoning_toggle": "🧠 LangChain Step-by-Step Chain-of-Thought Trace",
        "human_verification_checkpoints": "✅ Human Verification Checkpoints",
        "verify_scope_item": "Confirm authorization scope for '{category}' operations",
        "verify_accuracy_item": "Verify accuracy of pre-compiled outbound notification draft",
        "verify_biometric_item": "Execute biometric face match or SMS OTP validation before approval",
        "outbound_draft_toggle": "📤 Pre-Compiled Outbound Dispatch Draft",
        "teams_message_label": "Teams Message",
        "run_log_audit_header": "🛡️ RUN LOG EXECUTION AUDIT: {action} by {operator}",
        "run_log_toggle1_reasoning": "🔍 View Step-by-Step AI Reasoning Steps",
        "run_log_toggle2_payload": "📄 View Raw JSON Ingestion Payload",
        "turn_off_test_badge": "💡 Turn-Off Test: Rendered in native Notion blocks for offline inspection.",
        "step1_default": "[Step 1] Ingested raw payload and verified HMAC-SHA256 signature.",
        "step2_default": "[Step 2] Cognitive pre-audit completed and verified by human operator.",
        "step3_default": "[Step 3] Downstream dispatches triggered and sealed with cryptographic SHA-256 signature.",

        # Statuses
        "status_ready": "Ready for Review",
        "status_approved": "Approved",
        "status_dispatched": "Dispatched",
        "status_rejected": "Rejected",
        "status_healthy": "HEALTHY",

        # Dashboard UI
        "nav_command_center": "🎛️ Operations Command Center & Workflows",
        "nav_hitl": "📋 HITL Task Approvals",
        "nav_multiselect": "⚡ Notion Multi-Select Batch",
        "nav_biometrics": "🔐 Biometric & OTP Security Gate",
        "nav_webhook": "🧪 Webhook Ingestion Hub",
        "nav_scheduler": "⚙️ System Config & 60m Daemon",
        "nav_audit": "📊 SHA-256 Audit Ledger & Reports",

        "hero_badge": "ENTERPRISE ZERO-TRUST HITL PLATFORM",
        "hero_title": "Notion Tracker Control Portal",
        "hero_subtitle": "High-Availability Automation, Cognitive AI Pre-Audits & Non-Repudiation Audit Ledger",
        "active_operator": "Active Operator",
        "pipeline_active": "● Zero-Trust Pipeline Active",
        "language_selector_label": "🌐 Workspace Language:",
        "operator_profile": "👤 Operator Profile",
        "metric_pending": "Pending Review",
        "metric_approved": "Approved / Ready",
        "metric_dispatched": "Dispatched",
        "metric_critical": "Critical Risk",
        "token_telemetry": "⚡ Token-Bucket Telemetry",
        "available_tokens": "Available Tokens",
        "guard_status": "Guard Status",
        "system_health_title": "❤️ System Health (Turn-Off Test)",
        "cpu_load": "CPU Load",
        "ram_usage": "RAM Usage",
        "daemon_status": "Daemon Status",
        "uptime": "Uptime",
        "search_run_logs": "🔍 Search Run Logs:",
        "search_placeholder": "Filter by run name / title, provider, status, or keyword...",
        "filter_provider": "Filter by Provider / Source:",
        "filter_status": "Filter by Status / Action:",
        "all_providers": "All Providers",
        "all_statuses": "All Statuses",
        "btn_approve": "✅ Batch Approve & Trigger Dispatch",
        "btn_reject": "❌ Batch Reject Tasks",
        "btn_export_pdf": "📄 Download PDF Audit Report",
        "btn_export_excel": "📊 Download Tasks Excel / CSV",
        "audit_integrity_secure": "🟢 AUDIT LEDGER INTEGRITY: SECURE",
    },

    "es": {
        # Notion Typesetting Keys (Spanish)
        "ai_decision_engine": "🧠 Motor de Preauditoría y Decisión IA",
        "risk_evaluation_banner": "{emoji} EVALUACIÓN DE RIESGO PREVIA: {risk_level} (Confianza: {confidence}%)",
        "task_specifications": "📋 Especificaciones de Tarea y Carga Útil",
        "category_label": "Categoría",
        "requested_priority": "Prioridad Solicitada",
        "task_summary": "Resumen de Tarea",
        "cot_reasoning_toggle": "🧠 Rastreo de Cadena de Pensamiento LangChain Paso a Paso",
        "human_verification_checkpoints": "✅ Puntos de Verificación Humana",
        "verify_scope_item": "Confirmar alcance de autorización para operaciones de '{category}'",
        "verify_accuracy_item": "Verificar precisión del borrador de notificación de salida",
        "verify_biometric_item": "Ejecutar validación biométrica o SMS OTP antes de aprobar",
        "outbound_draft_toggle": "📤 Borrador de Envío Precompilado",
        "teams_message_label": "Mensaje de Teams",
        "run_log_audit_header": "🛡️ AUDITORÍA DE EJECUCIÓN DE REGISTRO: {action} por {operator}",
        "run_log_toggle1_reasoning": "🔍 Ver Pasos de Razonamiento de IA Paso a Paso",
        "run_log_toggle2_payload": "📄 Ver Carga Útil JSON Ingerida sin Procesar",
        "turn_off_test_badge": "💡 Prueba de Apagado: Renderizado en bloques nativos de Notion para inspección offline.",
        "step1_default": "[Paso 1] Carga útil sin procesar ingerida y firma HMAC-SHA256 verificada.",
        "step2_default": "[Paso 2] Preauditoría cognitiva completada y verificada por operador humano.",
        "step3_default": "[Paso 3] Envíos activados y sellados con firma criptográfica SHA-256.",

        # Statuses
        "status_ready": "Listo para Revisión",
        "status_approved": "Aprobado",
        "status_dispatched": "Despachado",
        "status_rejected": "Rechazado",
        "status_healthy": "SALUDABLE",

        # Dashboard UI
        "nav_command_center": "🎛️ Centro de Comando y Flujos de Trabajo",
        "nav_hitl": "📋 Aprobaciones de Tareas HITL",
        "nav_multiselect": "⚡ Selección Múltiple por Lotes Notion",
        "nav_biometrics": "🔐 Control Biométrico y Clave OTP",
        "nav_webhook": "🧪 Centro de Ingestión Webhook",
        "nav_scheduler": "⚙️ Configuración y Demonio 60m",
        "nav_audit": "📊 Libro de Auditoría SHA-256 e Informes",
        "hero_badge": "PLATAFORMA EMPRESARIAL HITL ZERO-TRUST",
        "hero_title": "Portal de Control Notion Tracker",
        "hero_subtitle": "Automatización de Alta Disponibilidad, Preauditorías de IA y Registro Inmutable",
        "active_operator": "Operador Activo",
        "pipeline_active": "● Canal Zero-Trust Activo",
        "language_selector_label": "🌐 Idioma del Espacio:",
        "operator_profile": "👤 Perfil de Operador",
        "metric_pending": "Pendiente de Revisión",
        "metric_approved": "Aprobado / Listo",
        "metric_dispatched": "Despachado",
        "metric_critical": "Riesgo Crítico",
        "token_telemetry": "⚡ Telemetría de Cubeta de Tokens",
        "available_tokens": "Tokens Disponibles",
        "guard_status": "Estado de Protección",
        "system_health_title": "❤️ Salud del Sistema (Prueba de Apagado)",
        "cpu_load": "Carga de CPU",
        "ram_usage": "Uso de RAM",
        "daemon_status": "Estado del Demonio",
        "uptime": "Tiempo Activo",
        "search_run_logs": "🔍 Buscar Registros de Ejecución:",
        "search_placeholder": "Filtrar por nombre de ejecución, proveedor, estado o palabra clave...",
        "filter_provider": "Filtrar por Proveedor / Origen:",
        "filter_status": "Filtrar por Estado / Acción:",
        "all_providers": "Todos los Proveedores",
        "all_statuses": "Todos los Estados",
        "btn_approve": "✅ Aprobar por Lote y Despachar",
        "btn_reject": "❌ Rechazar Tareas por Lote",
        "btn_export_pdf": "📄 Descargar Informe PDF",
        "btn_export_excel": "📊 Descargar Tareas Excel / CSV",
        "audit_integrity_secure": "🟢 INTEGRIDAD DEL REGISTRO: SEGURO",
    },

    "de": {
        # Notion Typesetting Keys (German)
        "ai_decision_engine": "🧠 KI-Vorabprüfung & Entscheidungs-Engine",
        "risk_evaluation_banner": "{emoji} {risk_level} RISIKO-VORABPRÜFUNGSEVALUIERUNG (Vertrauen: {confidence}%)",
        "task_specifications": "📋 Aufgabenspezifikationen & Nutzlast",
        "category_label": "Kategorie",
        "requested_priority": "Angeforderte Priorität",
        "task_summary": "Aufgabenzusammenfassung",
        "cot_reasoning_toggle": "🧠 LangChain Schritt-für-Schritt Gedankengang-Spur",
        "human_verification_checkpoints": "✅ Menschliche Verifizierungspunkte",
        "verify_scope_item": "Autorisierungsbereich für '{category}'-Operationen bestätigen",
        "verify_accuracy_item": "Genauigkeit des vorkompilierten Benachrichtigungsentwurfs überprüfen",
        "verify_biometric_item": "Biometrischen Gesichtsabgleich oder SMS-OTP vor Freigabe ausführen",
        "outbound_draft_toggle": "📤 Vorkompilierter Versandentwurf",
        "teams_message_label": "Teams-Nachricht",
        "run_log_audit_header": "🛡️ AUSFÜHRUNGSPROTOKOLL-AUDIT: {action} durch {operator}",
        "run_log_toggle1_reasoning": "🔍 Schritt-für-Schritt KI-Begründung anzeigen",
        "run_log_toggle2_payload": "📄 Rohe JSON-Ingestion-Nutzlast anzeigen",
        "turn_off_test_badge": "💡 Turn-Off-Test: In nativen Notion-Blöcken für Offline-Prüfung gerendert.",
        "step1_default": "[Schritt 1] Rohe Nutzlast aufgenommen und HMAC-SHA256-Signatur verifiziert.",
        "step2_default": "[Schritt 2] Kognitive Vorprüfung abgeschlossen und durch Operator bestätigt.",
        "step3_default": "[Schritt 3] Ausgehende Aktionen ausgelöst und mit SHA-256-Signatur versiegelt.",

        # Statuses
        "status_ready": "Bereit zur Prüfung",
        "status_approved": "Genehmigt",
        "status_dispatched": "Versendet",
        "status_rejected": "Abgelehnt",
        "status_healthy": "GESUND",

        # Dashboard UI
        "nav_command_center": "🎛️ Operations-Kommandozentrale & Workflows",
        "nav_hitl": "📋 HITL-Aufgabengenehmigungen",
        "nav_multiselect": "⚡ Notion Mehrfachauswahl-Batch",
        "nav_biometrics": "🔐 Biometrie- & OTP-Sicherheits-Gate",
        "nav_webhook": "🧪 Webhook-Ingestion-Hub",
        "nav_scheduler": "⚙️ Systemkonfiguration & 60m-Dienst",
        "nav_audit": "📊 SHA-256 Prüfprotokoll & Berichte",
        "hero_badge": "ENTERPRISE ZERO-TRUST HITL PLATTFORM",
        "hero_title": "Notion Tracker Steuerungsportal",
        "hero_subtitle": "Hochverfügbare Automatisierung, Kognitive KI-Prüfungen & Unveränderliches Audit-Ledger",
        "active_operator": "Aktiver Operator",
        "pipeline_active": "● Zero-Trust Pipeline Aktiv",
        "language_selector_label": "🌐 Workspace-Sprache:",
        "operator_profile": "👤 Operator-Profil",
        "metric_pending": "Ausstehende Prüfung",
        "metric_approved": "Genehmigt / Bereit",
        "metric_dispatched": "Versendet",
        "metric_critical": "Kritisches Risiko",
        "token_telemetry": "⚡ Token-Bucket Telemetrie",
        "available_tokens": "Verfügbare Tokens",
        "guard_status": "Schutzstatus",
        "system_health_title": "❤️ Systemgesundheit (Turn-Off-Test)",
        "cpu_load": "CPU-Auslastung",
        "ram_usage": "RAM-Nutzung",
        "daemon_status": "Dienst-Status",
        "uptime": "Betriebszeit",
        "search_run_logs": "🔍 Ausführungsprotokolle durchsuchen:",
        "search_placeholder": "Nach Name, Provider, Status oder Stichwort filtern...",
        "filter_provider": "Nach Provider / Quelle filtern:",
        "filter_status": "Nach Status / Aktion filtern:",
        "all_providers": "Alle Provider",
        "all_statuses": "Alle Status",
        "btn_approve": "✅ Batch genehmigen & versenden",
        "btn_reject": "❌ Aufgaben im Batch ablehnen",
        "btn_export_pdf": "📄 PDF-Prüfbericht herunterladen",
        "btn_export_excel": "📊 Aufgaben-Excel / CSV herunterladen",
        "audit_integrity_secure": "🟢 AUDIT-LEDGER-INTEGRITÄT: SICHER",
    },

    "ja": {
        # Notion Typesetting Keys (Japanese)
        "ai_decision_engine": "🧠 AI事前監査および意思決定エンジン",
        "risk_evaluation_banner": "{emoji} {risk_level} リスク事前監査評価 (信頼度: {confidence}%)",
        "task_specifications": "📋 タスク仕様およびペイロード",
        "category_label": "カテゴリー",
        "requested_priority": "要求された優先度",
        "task_summary": "タスクの概要",
        "cot_reasoning_toggle": "🧠 LangChain 思考プロセスのステップ追跡",
        "human_verification_checkpoints": "✅ 人間による検証チェックポイント",
        "verify_scope_item": "'{category}' 操作の承認権限範囲を確認",
        "verify_accuracy_item": "事前作成された外部通知ドラフトの正確性を確認",
        "verify_biometric_item": "承認前に生体認証（顔認証）またはSMS OTP検証を実行",
        "outbound_draft_toggle": "📤 事前生成された外部送信ドラフト",
        "teams_message_label": "Teams メッセージ",
        "run_log_audit_header": "🛡️ 実行ログ監査: {action} (オペレーター: {operator})",
        "run_log_toggle1_reasoning": "🔍 AIの思考プロセスをステップ毎に表示",
        "run_log_toggle2_payload": "📄 生のJSONペイロードを表示",
        "turn_off_test_badge": "💡 ターンオフテスト: サーバー停止時でもNotionネイティブブロックで閲覧可能。",
        "step1_default": "[ステップ1] 生のペイロードを受信しHMAC-SHA256署名を検証しました。",
        "step2_default": "[ステップ2] AI事前監査が完了し、人間オペレーターにより確認されました。",
        "step3_default": "[ステップ3] 外部配信がトリガーされ、SHA-256署名で封印されました。",

        # Statuses
        "status_ready": "レビュー待ち",
        "status_approved": "承認済み",
        "status_dispatched": "送信完了",
        "status_rejected": "却下",
        "status_healthy": "正常 (HEALTHY)",

        # Dashboard UI
        "nav_command_center": "🎛️ オペレーション コマンドセンター＆ワークフロー",
        "nav_hitl": "📋 HITL タスク承認",
        "nav_multiselect": "⚡ Notion マルチセレクト一括処理",
        "nav_biometrics": "🔐 生体認証＆OTPセキュリティゲート",
        "nav_webhook": "🧪 Webhook インジェスチョンハブ",
        "nav_scheduler": "⚙️ システム設定＆60分デーモン",
        "nav_audit": "📊 SHA-256 監査台帳＆レポート",
        "hero_badge": "エンタープライズ Zero-Trust HITL プラットフォーム",
        "hero_title": "Notion Tracker コントロールポータル",
        "hero_subtitle": "高可用性自動化、AI事前監査、暗号化改ざん防止台帳",
        "active_operator": "アクティブオペレーター",
        "pipeline_active": "● Zero-Trust パイプライン稼働中",
        "language_selector_label": "🌐 ワークスペース言語:",
        "operator_profile": "👤 オペレータープロファイル",
        "metric_pending": "レビュー待ち",
        "metric_approved": "承認済み / 準備完了",
        "metric_dispatched": "送信完了",
        "metric_critical": "重大リスク",
        "token_telemetry": "⚡ トークンバケット テレメトリ",
        "available_tokens": "利用可能トークン",
        "guard_status": "保護ステータス",
        "system_health_title": "❤️ システム健全性 (ターンオフテスト)",
        "cpu_load": "CPU 負荷",
        "ram_usage": "RAM 使用率",
        "daemon_status": "デーモン状態",
        "uptime": "稼働時間",
        "search_run_logs": "🔍 実行ログを検索:",
        "search_placeholder": "タスク名、プロバイダー、ステータス、キーワードで絞り込み...",
        "filter_provider": "プロバイダー / 送信元で絞り込み:",
        "filter_status": "ステータス / アクションで絞り込み:",
        "all_providers": "すべてのプロバイダー",
        "all_statuses": "すべてのステータス",
        "btn_approve": "✅ 一括承認して送信を実行",
        "btn_reject": "❌ タスクを一括却下",
        "btn_export_pdf": "📄 PDF 監査レポートをダウンロード",
        "btn_export_excel": "📊 タスク Excel / CSV をダウンロード",
        "audit_integrity_secure": "🟢 監査台帳の整合性: 安全 (SECURE)",
    },

    "hi": {
        # Notion Typesetting Keys (Hindi)
        "ai_decision_engine": "🧠 एआई पूर्व-ऑडिट और निर्णय इंजन",
        "risk_evaluation_banner": "{emoji} {risk_level} जोखिम पूर्व-ऑडिट मूल्यांकन (विश्वास: {confidence}%)",
        "task_specifications": "📋 कार्य विवरण और पेलोड",
        "category_label": "श्रेणी",
        "requested_priority": "अनुरोधित प्राथमिकता",
        "task_summary": "कार्य सारांश",
        "cot_reasoning_toggle": "🧠 लैंगचेन चरण-दर-चरण विचार श्रृंखला",
        "human_verification_checkpoints": "✅ मानव सत्यापन जांच बिंदु",
        "verify_scope_item": "'{category}' संचालन के लिए प्राधिकरण सीमा की पुष्टि करें",
        "verify_accuracy_item": "आउटबाउंड अधिसूचना ड्राफ्ट की सटीकता सत्यापित करें",
        "verify_biometric_item": "स्वीकृति से पहले बायोमेट्रिक चेहरा मिलान या एसएमएस ओटीपी सत्यापित करें",
        "outbound_draft_toggle": "📤 पूर्व-संकलित आउटबाउंड डिस्पैच ड्राफ्ट",
        "teams_message_label": "टीम्स संदेश",
        "run_log_audit_header": "🛡️ रन लॉग निष्पादन ऑडिट: {action} द्वारा {operator}",
        "run_log_toggle1_reasoning": "🔍 चरण-दर-चरण एआई तर्क देखें",
        "run_log_toggle2_payload": "📄 कच्चा JSON पेलोड देखें",
        "turn_off_test_badge": "💡 टर्न-ऑफ टेस्ट: सर्वर बंद होने पर भी नोशन नेटिव ब्लॉक्स में उपलब्ध।",
        "step1_default": "[चरण 1] कच्चा पेलोड प्राप्त हुआ और HMAC-SHA256 हस्ताक्षर सत्यापित किया गया।",
        "step2_default": "[चरण 2] संज्ञानात्मक पूर्व-ऑडिट पूर्ण और मानव ऑपरेटर द्वारा सत्यापित।",
        "step3_default": "[चरण 3] आउटबाउंड डिस्पैच सक्रिय और SHA-256 हस्ताक्षर द्वारा सुरक्षित।",

        # Statuses
        "status_ready": "समीक्षा के लिए तैयार",
        "status_approved": "स्वीकृत",
        "status_dispatched": "भेजा गया",
        "status_rejected": "अस्वीकृत",
        "status_healthy": "स्वस्थ (HEALTHY)",

        # Dashboard UI
        "nav_command_center": "🎛️ संचालन कमांड सेंटर और वर्कफ़्लो",
        "nav_hitl": "📋 एचआईटीएल कार्य स्वीकृतियां",
        "nav_multiselect": "⚡ नोशन मल्टी-सिलेक्ट बैच",
        "nav_biometrics": "🔐 बायोमेट्रिक और ओटीपी सुरक्षा द्वार",
        "nav_webhook": "🧪 वेबहुक इनजेशन हब",
        "nav_scheduler": "⚙️ सिस्टम कॉन्फ़िग और 60 मिनट डेमन",
        "nav_audit": "📊 SHA-256 ऑडिट बहीखाता और रिपोर्ट",
        "hero_badge": "एंटरप्राइज ज़ीरो-ट्रस्ट एचआईटीएल प्लेटफॉर्म",
        "hero_title": "नोशन ट्रैकर कंट्रोल पोर्टल",
        "hero_subtitle": "उच्च-उपलब्धता स्वचालन, संज्ञानात्मक एआई ऑडिट और अपरिवर्तनीय बहीखाता",
        "active_operator": "सक्रिय ऑपरेटर",
        "pipeline_active": "● ज़ीरो-ट्रस्ट पाइपलाइन सक्रिय",
        "language_selector_label": "🌐 कार्यक्षेत्र भाषा:",
        "operator_profile": "👤 ऑपरेटर प्रोफ़ाइल",
        "metric_pending": "समीक्षा लंबित",
        "metric_approved": "स्वीकृत / तैयार",
        "metric_dispatched": "भेजा गया",
        "metric_critical": "गंभीर जोखिम",
        "token_telemetry": "⚡ टोकन-बकेट टेलीमेट्री",
        "available_tokens": "उपलब्ध टोकन",
        "guard_status": "सुरक्षा स्थिति",
        "system_health_title": "❤️ सिस्टम स्वास्थ्य (टर्न-ऑफ टेस्ट)",
        "cpu_load": "सीपीयू लोड",
        "ram_usage": "रैम उपयोग",
        "daemon_status": "डेमन स्थिति",
        "uptime": "अपटाइम",
        "search_run_logs": "🔍 रन लॉग खोजें:",
        "search_placeholder": "कार्य नाम, प्रदाता, स्थिति या कीवर्ड द्वारा फ़िल्टर करें...",
        "filter_provider": "प्रदाता / स्रोत द्वारा फ़िल्टर करें:",
        "filter_status": "स्थिति / क्रिया द्वारा फ़िल्टर करें:",
        "all_providers": "सभी प्रदाता",
        "all_statuses": "सभी स्थितियां",
        "btn_approve": "✅ बैच स्वीकृत करें और डिस्पैच शुरू करें",
        "btn_reject": "❌ बैच कार्य अस्वीकार करें",
        "btn_export_pdf": "📄 पीडीएफ ऑडिट रिपोर्ट डाउनलोड करें",
        "btn_export_excel": "📊 कार्य एक्सेल / सीएसवी डाउनलोड करें",
        "audit_integrity_secure": "🟢 ऑडिट बहीखाता अखंडता: सुरक्षित (SECURE)",
    },

    "fr": {
        # Notion Typesetting Keys (French)
        "ai_decision_engine": "🧠 Moteur de Pré-Audit et Décision IA",
        "risk_evaluation_banner": "{emoji} ÉVALUATION DES RISQUES: {risk_level} (Confiance: {confidence}%)",
        "task_specifications": "📋 Spécifications de Tâche et Charge Utile",
        "category_label": "Catégorie",
        "requested_priority": "Priorité Demandée",
        "task_summary": "Résumé de Tâche",
        "cot_reasoning_toggle": "🧠 Trace de Raisonnement LangChain Étape par Étape",
        "human_verification_checkpoints": "✅ Points de Contrôle Humain",
        "verify_scope_item": "Confirmer le périmètre d'autorisation pour les opérations '{category}'",
        "verify_accuracy_item": "Vérifier l'exactitude du brouillon de notification sortant",
        "verify_biometric_item": "Exécuter la validation biométrique ou SMS OTP avant approbation",
        "outbound_draft_toggle": "📤 Projet d'Envoi Sortant Précompilé",
        "teams_message_label": "Message Teams",
        "run_log_audit_header": "🛡️ AUDIT D'EXÉCUTION DU JOURNAL: {action} par {operator}",
        "run_log_toggle1_reasoning": "🔍 Afficher les Étapes de Raisonnement IA",
        "run_log_toggle2_payload": "📄 Afficher la Charge Utile JSON Brute Ingestée",
        "turn_off_test_badge": "💡 Test d'Extinction: Rendu en blocs natifs Notion pour inspection hors ligne.",
        "step1_default": "[Étape 1] Charge utile brute ingérée et signature HMAC-SHA256 vérifiée.",
        "step2_default": "[Étape 2] Pré-audit cognitif complété et validé par un opérateur humain.",
        "step3_default": "[Étape 3] Envois déclenchés et scellés avec signature cryptographique SHA-256.",

        # Statuses
        "status_ready": "Prêt pour Révision",
        "status_approved": "Approuvé",
        "status_dispatched": "Envoyé",
        "status_rejected": "Rejeté",
        "status_healthy": "SAIN (HEALTHY)",

        # Dashboard UI
        "nav_command_center": "🎛️ Centre de Commandement et Flux de Travail",
        "nav_hitl": "📋 Approbations de Tâches HITL",
        "nav_multiselect": "⚡ Sélection Multiple par Lots Notion",
        "nav_biometrics": "🔐 Contrôle Biométrique et Clé OTP",
        "nav_webhook": "🧪 Hub d'Ingestion Webhook",
        "nav_scheduler": "⚙️ Configuration Système & Démon 60m",
        "nav_audit": "📊 Registre d'Audit SHA-256 & Rapports",
        "hero_badge": "PLATEFORME ENTERPRISE HITL ZERO-TRUST",
        "hero_title": "Portail de Contrôle Notion Tracker",
        "hero_subtitle": "Automatisation Haute Disponibilité, Pré-audits IA et Registre Immuable",
        "active_operator": "Opérateur Actif",
        "pipeline_active": "● Pipeline Zero-Trust Actif",
        "language_selector_label": "🌐 Langue de l'Espace:",
        "operator_profile": "👤 Profil de l'Opérateur",
        "metric_pending": "En Attente de Révision",
        "metric_approved": "Approuvé / Prêt",
        "metric_dispatched": "Envoyé",
        "metric_critical": "Risque Critique",
        "token_telemetry": "⚡ Télémétrie Seau de Jetons",
        "available_tokens": "Jetons Disponibles",
        "guard_status": "État de Protection",
        "system_health_title": "❤️ Santé du Système (Test d'Extinction)",
        "cpu_load": "Charge CPU",
        "ram_usage": "Utilisation RAM",
        "daemon_status": "Statut du Démon",
        "uptime": "Temps d'Activité",
        "search_run_logs": "🔍 Rechercher dans les Journaux:",
        "search_placeholder": "Filtrer par nom, fournisseur, statut ou mot-clé...",
        "filter_provider": "Filtrer par Fournisseur / Source:",
        "filter_status": "Filtrer par Statut / Action:",
        "all_providers": "Tous les Fournisseurs",
        "all_statuses": "Tous les Statuts",
        "btn_approve": "✅ Approuver par Lot et Déclencher l'Envoi",
        "btn_reject": "❌ Rejeter les Tâches par Lot",
        "btn_export_pdf": "📄 Télécharger Rapport PDF",
        "btn_export_excel": "📊 Télécharger Tâches Excel / CSV",
        "audit_integrity_secure": "🟢 INTÉGRITÉ DU REGISTRE: SÉCURISÉ",
    }

}


def get_current_language() -> str:
    """Retrieves the globally configured workspace language code."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("language", "en")
        except Exception:
            pass
    return "en"


def set_current_language(lang_code: str) -> None:
    """Persists the workspace language code to system configuration."""
    if lang_code not in TRANSLATIONS:
        lang_code = "en"
    current = {}
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                current = json.load(f)
        except Exception:
            current = {}
    current["language"] = lang_code
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
    except Exception:
        pass


def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """Translates a localization key into the target language with string interpolation.

    Args:
        key: The lookup key in the translation dictionary.
        lang: Target language code ('en', 'es', 'de', 'ja', 'hi', 'fr'). Defaults to current config.
        **kwargs: Dynamic format arguments to interpolate into the translated string.

    Returns:
        Translated string or English fallback if not found.
    """
    if not lang:
        lang = get_current_language()

    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    template = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))

    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
