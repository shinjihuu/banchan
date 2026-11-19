/**
 * 인도사랑 반찬가게 — 주문 저장용 구글 시트 스크립트
 *
 * 1) 구글 시트 → 확장 프로그램 → Apps Script 에 이 내용을 통째로 붙여넣기
 * 2) 아래 TOKEN 을 아무도 모르는 긴 문자로 바꾸기 (Streamlit Secrets 의 SHEET_TOKEN 과 같게)
 * 3) 배포 → 새 배포 → 유형: 웹 앱 → 실행: 나 / 액세스: 모든 사용자 → 배포
 * 4) 나온 웹 앱 URL 을 Streamlit Secrets 의 SHEET_URL 에 넣기
 */
const TOKEN = '여기에_비밀문자를_넣으세요';
const SHEET_NAME = '주문';
const HEADERS = ['주문번호', '주문시간', '전도회', '이름', '총각김치', '새송이버섯계란장조림', '제육볶음', '금액'];

function sheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  if (sh.getLastRow() === 0) {
    sh.getRange('A:D').setNumberFormat('@'); // 주문번호·시간·전도회·이름은 글자 그대로 저장
    sh.appendRow(HEADERS);
    sh.setFrozenRows(1);
  }
  return sh;
}

function out_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function toRow_(o) {
  return HEADERS.map(function (h) { return o[h] === undefined || o[h] === null ? '' : o[h]; });
}

// 주문 목록 읽기
function doGet(e) {
  if (!e || e.parameter.token !== TOKEN) return out_({ ok: false, error: 'token' });
  return out_({ ok: true, rows: sheet_().getDataRange().getDisplayValues() });
}

// 주문 추가(append) / 전체 저장(replace)
function doPost(e) {
  let body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false, error: 'bad json' }); }
  if (body.token !== TOKEN) return out_({ ok: false, error: 'token' });

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const sh = sheet_();
    if (body.action === 'append') {
      sh.appendRow(toRow_(body.row));
    } else if (body.action === 'replace') {
      sh.clearContents();
      sh.getRange('A:D').setNumberFormat('@');
      sh.appendRow(HEADERS);
      if (body.rows.length) {
        sh.getRange(2, 1, body.rows.length, HEADERS.length).setValues(body.rows.map(toRow_));
      }
    } else {
      return out_({ ok: false, error: 'unknown action' });
    }
    return out_({ ok: true });
  } finally {
    lock.releaseLock();
  }
}
