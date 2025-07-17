/**
 * FusionCRM Google Apps Script バックエンド
 * Streamlit FusionCRMとGoogle Sheetsを連携
 */

// 設定定数
const SPREADSHEET_NAME = "FusionCRM Database";
const COMPANIES_SHEET_NAME = "Companies";
const HISTORY_SHEET_NAME = "Status_History";

/**
 * スプレッドシートとシートを取得または作成
 */
function getOrCreateSpreadsheet() {
  // 既存のスプレッドシートを検索
  const files = DriveApp.getFilesByName(SPREADSHEET_NAME);
  let spreadsheet;
  
  if (files.hasNext()) {
    // 既存のスプレッドシートを使用
    spreadsheet = SpreadsheetApp.open(files.next());
  } else {
    // 新しいスプレッドシートを作成
    spreadsheet = SpreadsheetApp.create(SPREADSHEET_NAME);
    
    // 企業データシートを設定
    const companiesSheet = spreadsheet.getActiveSheet();
    companiesSheet.setName(COMPANIES_SHEET_NAME);
    
    // ヘッダーを設定
    const headers = [
      "ID", "企業名", "業界", "ウェブサイト", "担当者", "メール", "電話", 
      "PicoCELA関連度", "ステータス", "備考", "作成日", "最終更新日"
    ];
    companiesSheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    
    // 履歴シートを作成
    const historySheet = spreadsheet.insertSheet(HISTORY_SHEET_NAME);
    const historyHeaders = [
      "ID", "企業ID", "企業名", "変更前ステータス", "変更後ステータス", 
      "変更理由", "変更者", "変更日時"
    ];
    historySheet.getRange(1, 1, 1, historyHeaders.length).setValues([historyHeaders]);
    
    // シートを共有可能に設定
    DriveApp.getFileById(spreadsheet.getId()).setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.EDIT);
  }
  
  return spreadsheet;
}

/**
 * 企業データシートを取得
 */
function getCompaniesSheet() {
  const spreadsheet = getOrCreateSpreadsheet();
  let sheet = spreadsheet.getSheetByName(COMPANIES_SHEET_NAME);
  
  if (!sheet) {
    sheet = spreadsheet.insertSheet(COMPANIES_SHEET_NAME);
    const headers = [
      "ID", "企業名", "業界", "ウェブサイト", "担当者", "メール", "電話", 
      "PicoCELA関連度", "ステータス", "備考", "作成日", "最終更新日"
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }
  
  return sheet;
}

/**
 * 履歴シートを取得
 */
function getHistorySheet() {
  const spreadsheet = getOrCreateSpreadsheet();
  let sheet = spreadsheet.getSheetByName(HISTORY_SHEET_NAME);
  
  if (!sheet) {
    sheet = spreadsheet.insertSheet(HISTORY_SHEET_NAME);
    const headers = [
      "ID", "企業ID", "企業名", "変更前ステータス", "変更後ステータス", 
      "変更理由", "変更者", "変更日時"
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }
  
  return sheet;
}

/**
 * ユニークIDを生成
 */
function generateId() {
  return "CMP_" + Utilities.getUuid().substring(0, 8);
}

/**
 * すべての企業データを取得
 */
function getCompanies() {
  try {
    const sheet = getCompaniesSheet();
    const lastRow = sheet.getLastRow();
    
    if (lastRow <= 1) {
      return [];
    }
    
    const data = sheet.getRange(2, 1, lastRow - 1, 12).getValues();
    const companies = [];
    
    data.forEach(row => {
      if (row[0]) { // IDが存在する行のみ
        companies.push({
          id: row[0],
          name: row[1],
          industry: row[2],
          website: row[3],
          contact_person: row[4],
          email: row[5],
          phone: row[6],
          picoCela_score: row[7],
          status: row[8],
          notes: row[9],
          created_date: row[10],
          last_updated: row[11]
        });
      }
    });
    
    return companies;
  } catch (error) {
    console.error("企業データ取得エラー:", error);
    throw new Error("企業データの取得に失敗しました: " + error.toString());
  }
}

/**
 * 新しい企業を追加
 */
function addCompany(companyData) {
  try {
    const sheet = getCompaniesSheet();
    const id = generateId();
    const now = new Date();
    
    const rowData = [
      id,
      companyData.name,
      companyData.industry || "",
      companyData.website || "",
      companyData.contact_person || "",
      companyData.email || "",
      companyData.phone || "",
      companyData.picoCela_score || 5,
      companyData.status || "New",
      companyData.notes || "",
      companyData.created_date || now,
      now
    ];
    
    sheet.appendRow(rowData);
    
    return {
      success: true,
      message: "企業が正常に追加されました",
      id: id
    };
  } catch (error) {
    console.error("企業追加エラー:", error);
    throw new Error("企業の追加に失敗しました: " + error.toString());
  }
}

/**
 * 企業ステータスを更新
 */
function updateCompanyStatus(companyId, newStatus, note = "") {
  try {
    const sheet = getCompaniesSheet();
    const data = sheet.getDataRange().getValues();
    
    // 企業を検索
    let rowIndex = -1;
    let currentStatus = "";
    let companyName = "";
    
    for (let i = 1; i < data.length; i++) {
      if (data[i][0] === companyId) {
        rowIndex = i + 1;
        currentStatus = data[i][8];
        companyName = data[i][1];
        break;
      }
    }
    
    if (rowIndex === -1) {
      throw new Error("指定された企業が見つかりません");
    }
    
    // ステータスと最終更新日を更新
    sheet.getRange(rowIndex, 9).setValue(newStatus); // ステータス列
    sheet.getRange(rowIndex, 12).setValue(new Date()); // 最終更新日列
    
    // 履歴を記録
    addStatusHistory(companyId, companyName, currentStatus, newStatus, note);
    
    return {
      success: true,
      message: `ステータスを ${currentStatus} から ${newStatus} に更新しました`
    };
  } catch (error) {
    console.error("ステータス更新エラー:", error);
    throw new Error("ステータスの更新に失敗しました: " + error.toString());
  }
}

/**
 * ステータス変更履歴を追加
 */
function addStatusHistory(companyId, companyName, oldStatus, newStatus, note) {
  try {
    const historySheet = getHistorySheet();
    const historyId = "HST_" + Utilities.getUuid().substring(0, 8);
    
    const historyData = [
      historyId,
      companyId,
      companyName,
      oldStatus,
      newStatus,
      note || "",
      Session.getActiveUser().getEmail(),
      new Date()
    ];
    
    historySheet.appendRow(historyData);
  } catch (error) {
    console.error("履歴追加エラー:", error);
    // 履歴の失敗は致命的ではないので、ログのみ
  }
}

/**
 * Webアプリのメインエントリーポイント
 */
function doPost(e) {
  try {
    // CORS対応
    const response = {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
      }
    };
    
    if (!e.postData) {
      throw new Error("リクエストデータがありません");
    }
    
    const requestData = JSON.parse(e.postData.contents);
    const action = requestData.action;
    
    let result;
    
    switch (action) {
      case "ping":
        result = {
          status: "success",
          message: "FusionCRM バックエンドが正常に動作しています",
          timestamp: new Date().toISOString()
        };
        break;
        
      case "getCompanies":
        const companies = getCompanies();
        result = {
          status: "success",
          data: companies,
          count: companies.length
        };
        break;
        
      case "addCompany":
        const addResult = addCompany(requestData.data);
        result = {
          status: "success",
          message: addResult.message,
          id: addResult.id
        };
        break;
        
      case "updateStatus":
        const updateResult = updateCompanyStatus(
          requestData.companyId,
          requestData.status,
          requestData.note
        );
        result = {
          status: "success",
          message: updateResult.message
        };
        break;
        
      default:
        throw new Error(`未知のアクション: ${action}`);
    }
    
    return ContentService
      .createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    console.error("リクエスト処理エラー:", error);
    
    const errorResult = {
      status: "error",
      message: error.toString(),
      timestamp: new Date().toISOString()
    };
    
    return ContentService
      .createTextOutput(JSON.stringify(errorResult))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * GET リクエスト対応（テスト用）
 */
function doGet(e) {
  const testResult = {
    status: "success",
    message: "FusionCRM Google Apps Script バックエンドが稼働中です",
    version: "1.0.0",
    timestamp: new Date().toISOString(),
    spreadsheetUrl: getOrCreateSpreadsheet().getUrl()
  };
  
  return ContentService
    .createTextOutput(JSON.stringify(testResult))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * テスト関数: 手動でデータベースをセットアップ
 */
function setupDatabase() {
  try {
    const spreadsheet = getOrCreateSpreadsheet();
    console.log("データベースセットアップ完了");
    console.log("スプレッドシートURL:", spreadsheet.getUrl());
    
    // テストデータを追加
    const testCompany = {
      name: "テスト建設株式会社",
      industry: "建設業",
      website: "https://test-construction.com",
      contact_person: "山田太郎",
      email: "yamada@test-construction.com",
      phone: "03-1234-5678",
      picoCela_score: 8,
      status: "New",
      notes: "メッシュネットワークに興味あり"
    };
    
    addCompany(testCompany);
    console.log("テストデータ追加完了");
    
  } catch (error) {
    console.error("セットアップエラー:", error);
  }
}