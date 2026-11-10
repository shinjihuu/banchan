# 🍱 사랑의 반찬 나눔 주문표

Streamlit 반찬 주문 앱입니다.

- **테이블 1 (주문 입력)**: 전도회 선택(4~16, 결새모) → 이름 입력 → 반찬 수량 입력 → 금액 자동 계산 (반찬 1개당 10,000원)
- **테이블 2 (전도회별 집계)**: 전도회별 누적 반찬 수량과 금액, 전체 합계

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 설정 변경
`app.py` 상단의 `PRICE`, `GROUPS`, `DISHES` 값을 바꾸면 가격·전도회·반찬 종류를 수정할 수 있습니다.

## 데이터 저장
주문은 `orders.csv`에 자동 저장됩니다. Streamlit Community Cloud는 앱이 재시작(재배포·장시간 미사용)되면 파일이 초기화되므로, 마감 후에는 **CSV 다운로드** 버튼으로 꼭 백업하세요.
