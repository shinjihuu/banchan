# 🍱 인도사랑 반찬가게

휴대폰 세로 화면에 맞춘 Streamlit 반찬 주문 앱입니다.

## 주문 화면 (링크 받은 분)
1. 전도회 선택(4~16, 결새모) + 이름 입력
2. 반찬 카드에서 **+ / −** 로 장바구니에 담기 (반찬 1개당 10,000원)
3. 장바구니 확인 → **주문하기**
   다른 사람의 주문은 보이지 않습니다. (금요철야 예배 후까지 수령 안내 문구 표시)

## 관리자 화면
주문 화면 맨 아래 **🔒 관리자** → 비밀번호 입력
- 전도회별 명단 (이름, 반찬, 금액)
- 전도회별 집계표
- 주문 수정·삭제
- **엑셀 다운로드**: `전도회별 집계`, `전체 주문`, 전도회마다 명단 시트

### 관리자 비밀번호 설정 (필수)
Streamlit Community Cloud → 앱 **Settings → Secrets** 에 입력:
```toml
ADMIN_PASSWORD = "원하는비밀번호"
```
로컬에서는 `.streamlit/secrets.toml` 에 같은 내용을 넣으면 됩니다 (git에 올라가지 않음).

## 반찬 사진 (누끼)
`images/kimchi.png`, `images/jangjorim.png`, `images/jeyuk.png` 가 있으면 이모지 대신 사진이 보입니다.
원본 사진으로 투명 배경 PNG 만들기:
```bash
pip install "rembg[cpu]" pillow
python tools/cutout.py 총각김치.jpg kimchi
python tools/cutout.py 장조림.jpg jangjorim
python tools/cutout.py 제육볶음.jpg jeyuk
```

## 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 설정 변경
`app.py` 위쪽의 `PRICE`(가격), `GROUPS`(전도회), `MENU`(반찬 이름·화면 표시 이름·사진), `PICKUP_NOTICE`(수령 안내 문구)를 바꾸면 됩니다.

## 데이터 저장 주의
주문은 서버의 `orders.csv`에 저장됩니다. Streamlit Cloud는 앱이 재시작(재배포·장시간 미사용)되면 이 파일이 초기화되므로,
마감 후 관리자 화면에서 **엑셀 다운로드**로 꼭 백업하세요.
