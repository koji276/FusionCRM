"""
データインポート機能モジュール
fusion_crm_main.pyから抽出
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from .data_processor import DataImportProcessor
from .constants import IMPORT_SETTINGS


def show_data_import(company_manager):
    """データインポート機能（完全実装版）"""
    st.header("📁 データインポート")
    
    tab1, tab2, tab3 = st.tabs(["📤 ファイルアップロード", "📊 データプレビュー", "📋 インポート履歴"])
    
    with tab1:
        st.subheader("📤 企業データのインポート")
        st.info("Excel (XLSX)、CSV、TSVファイルに対応しています。")
        
        # ファイルアップロード
        uploaded_file = st.file_uploader(
            "ファイルを選択してください",
            type=['xlsx', 'xls', 'csv', 'tsv'],
            help="企業データを含むファイルをアップロードしてください"
        )
        
        if uploaded_file is not None:
            try:
                # ファイルタイプに応じた処理
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(uploaded_file)
                elif uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith('.tsv'):
                    df = pd.read_csv(uploaded_file, sep='\t')
                
                st.success(f"✅ ファイル読み込み成功: {len(df)}行のデータ")
                
                # データプレビュー
                st.subheader("📊 データプレビュー")
                st.dataframe(df.head(10), use_container_width=True)
                
                # カラムマッピング設定
                st.subheader("🔄 カラムマッピング")
                st.info("アップロードファイルのカラムを FusionCRM の項目にマッピングしてください")
                
                # FusionCRMの標準カラム
                fusion_columns = IMPORT_SETTINGS['fusion_columns']
                
                # 自動マッピング提案
                auto_mapping = DataImportProcessor.suggest_column_mapping(df.columns.tolist())
                
                # マッピング設定UI
                mapping = {}
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**FusionCRM項目**")
                    for fusion_col, description in fusion_columns.items():
                        st.markdown(f"• **{description}**")
                
                with col2:
                    st.markdown("**ファイルのカラム**")
                    for fusion_col, description in fusion_columns.items():
                        suggested = auto_mapping.get(fusion_col, '')
                        options = ['（マッピングしない）'] + df.columns.tolist()
                        
                        default_index = 0
                        if suggested and suggested in df.columns:
                            default_index = options.index(suggested)
                        
                        selected = st.selectbox(
                            description,
                            options,
                            index=default_index,
                            key=f"mapping_{fusion_col}"
                        )
                        
                        if selected != '（マッピングしない）':
                            mapping[fusion_col] = selected
                
                # 詳細設定
                st.subheader("⚙️ インポート設定")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    import_mode = st.radio(
                        "インポートモード",
                        ["新規追加のみ", "重複チェック（メールアドレス基準）", "すべて追加"]
                    )
                    
                    batch_size = st.number_input(
                        "バッチサイズ",
                        min_value=1,
                        max_value=100,
                        value=10,
                        help="一度に処理する企業数"
                    )
                
                with col2:
                    auto_wifi_detection = st.checkbox(
                        "WiFi需要の自動判定",
                        value=True,
                        help="企業名・説明からWiFi需要を自動判定"
                    )
                    
                    auto_picocela_scoring = st.checkbox(
                        "PicoCELA関連度の自動計算",
                        value=True,
                        help="キーワードマッチングによる関連度計算"
                    )
                
                # プレビュー変換
                if st.button("🔍 変換プレビュー", type="secondary"):
                    if 'company_name' not in mapping:
                        st.error("❌ 企業名のマッピングは必須です")
                    else:
                        preview_df = DataImportProcessor.create_import_preview(df, mapping, auto_wifi_detection, auto_picocela_scoring)
                        st.subheader("📋 変換後データプレビュー（最初の5行）")
                        st.dataframe(preview_df.head(), use_container_width=True)
                        
                        # 統計情報
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            wifi_count = len(preview_df[preview_df['wifi_required'] == 1]) if 'wifi_required' in preview_df.columns else 0
                            st.metric("WiFi需要企業", wifi_count)
                        
                        with col2:
                            high_relevance = len(preview_df[preview_df['picocela_relevance_score'] >= 50]) if 'picocela_relevance_score' in preview_df.columns else 0
                            st.metric("高関連度企業", high_relevance)
                        
                        with col3:
                            total_valid = len(preview_df[preview_df['company_name'].notna() & (preview_df['company_name'] != '')])
                            st.metric("有効データ", total_valid)
                
                # インポート実行
                st.subheader("🚀 インポート実行")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📥 データインポート開始", type="primary", use_container_width=True):
                        if 'company_name' not in mapping:
                            st.error("❌ 企業名のマッピングは必須です")
                        else:
                            execute_data_import(
                                df, mapping, company_manager, 
                                import_mode, batch_size,
                                auto_wifi_detection, auto_picocela_scoring
                            )
                
                with col2:
                    if st.button("📄 CSVエクスポート", type="secondary", use_container_width=True):
                        if 'company_name' in mapping:
                            export_df = DataImportProcessor.create_import_preview(df, mapping, auto_wifi_detection, auto_picocela_scoring)
                            csv = export_df.to_csv(index=False)
                            st.download_button(
                                label="📥 変換後データをダウンロード",
                                data=csv,
                                file_name=f"fusioncrm_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.error("❌ まず企業名のマッピングを設定してください")
                            
            except Exception as e:
                st.error(f"❌ ファイル読み込みエラー: {str(e)}")
    
    with tab2:
        st.subheader("📊 データプレビュー・検証")
        st.info("アップロードしたデータの詳細分析を行います")
        
        # 既存のアップロードファイルがあるかチェック
        if 'uploaded_file' in locals() and uploaded_file is not None:
            # データ品質チェック
            DataImportProcessor.show_data_quality_analysis(df)
        else:
            st.info("📤 まずファイルをアップロードしてください")
    
    with tab3:
        st.subheader("📋 インポート履歴")
        show_import_history()


def execute_data_import(df, mapping, company_manager, import_mode, batch_size, auto_wifi, auto_picocela):
    """データインポートの実行"""
    
    # プログレスバーの初期化
    progress_bar = st.progress(0)
    status_text = st.empty()
    stats_container = st.container()
    
    # 統計情報の初期化
    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    # 変換後データの作成
    import_df = DataImportProcessor.create_import_preview(df, mapping, auto_wifi, auto_picocela)
    total_rows = len(import_df)
    
    if total_rows == 0:
        st.error("❌ インポート可能なデータがありません")
        return
    
    status_text.text(f"📥 {total_rows}社のデータをインポート中...")
    
    # バッチ処理でインポート
    for i in range(0, total_rows, batch_size):
        batch_df = import_df.iloc[i:i+batch_size]
        
        for idx, row in batch_df.iterrows():
            try:
                # 企業データの準備
                company_data = row.to_dict()
                
                # 重複チェック（メールアドレス基準）
                if import_mode == "重複チェック（メールアドレス基準）" and company_data.get('email'):
                    # 既存企業の確認
                    existing_companies = company_manager.get_all_companies()
                    if not existing_companies.empty and 'email' in existing_companies.columns:
                        if company_data['email'] in existing_companies['email'].values:
                            stats['skipped'] += 1
                            continue
                
                # 企業追加
                result = company_manager.add_company(company_data, user_id='data_import')
                
                if result:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
                    stats['errors'].append(f"企業追加失敗: {company_data.get('company_name', 'Unknown')}")
                
                stats['total'] += 1
                
                # プログレスバー更新
                progress = (stats['total']) / total_rows
                progress_bar.progress(progress)
                status_text.text(f"📥 処理中... {stats['total']}/{total_rows} ({stats['success']}成功, {stats['failed']}失敗, {stats['skipped']}スキップ)")
                
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"エラー: {str(e)} (企業: {company_data.get('company_name', 'Unknown')})")
        
        # バッチ間の小休止
        time.sleep(0.1)
    
    # 完了メッセージ
    progress_bar.progress(1.0)
    
    if stats['success'] > 0:
        st.success(f"✅ インポート完了! {stats['success']}社を正常に追加しました")
    
    # 詳細統計
    with stats_container:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("✅ 成功", stats['success'])
        with col2:
            st.metric("❌ 失敗", stats['failed'])
        with col3:
            st.metric("⏭️ スキップ", stats['skipped'])
        with col4:
            st.metric("📊 処理総数", stats['total'])
    
    # エラー詳細
    if stats['errors']:
        with st.expander(f"❌ エラー詳細 ({len(stats['errors'])}件)"):
            for error in stats['errors'][:10]:  # 最初の10件のみ表示
                st.text(error)
            if len(stats['errors']) > 10:
                st.text(f"... その他 {len(stats['errors']) - 10} 件のエラー")
    
    # インポート履歴の保存
    save_import_history(stats, mapping, import_mode)


def save_import_history(stats, mapping, import_mode):
    """インポート履歴の保存"""
    if 'import_history' not in st.session_state:
        st.session_state.import_history = []
    
    history_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stats': stats,
        'mapping': mapping,
        'import_mode': import_mode
    }
    
    st.session_state.import_history.append(history_entry)


def show_import_history():
    """インポート履歴の表示"""
    if 'import_history' not in st.session_state or not st.session_state.import_history:
        st.info("📋 インポート履歴がありません")
        return
    
    st.markdown("**📊 最近のインポート履歴**")
    
    for i, entry in enumerate(reversed(st.session_state.import_history[-10:])):
        with st.expander(f"📅 {entry['timestamp']} - {entry['stats']['success']}社追加"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**統計情報**")
                st.json(entry['stats'])
            
            with col2:
                st.markdown("**設定情報**")
                st.text(f"インポートモード: {entry['import_mode']}")
                st.markdown("**カラムマッピング:**")
                for fusion_col, file_col in entry['mapping'].items():
                    st.text(f"• {fusion_col} ← {file_col}")
    
    # 履歴クリア
    if st.button("🗑️ 履歴をクリア"):
        st.session_state.import_history = []
        st.rerun()
