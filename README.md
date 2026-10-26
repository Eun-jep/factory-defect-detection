# factory-defect-detection

제조 설비 데이터 수집 → 저장 → AI 불량 판정 시스템 (Python, PyTorch, MariaDB, Streamlit)

## 프로젝트 소개
가상 설비가 제품 정보를 서버로 보내면, AI가 제품 사진을 보고 정상/불량을 판정하고, 결과를 MariaDB에 저장해 대시보드로 보여주는 시스템입니다.

## 개발 환경
- Python, PyTorch 2.11 (Google Colab, Tesla T4 GPU)
- MariaDB 11.8.6 (WSL)
- Streamlit (예정)

## 데이터셋
- MVTec AD (bottle 카테고리), 라이선스 CC BY-NC-SA 4.0
- 실제 설비 데이터를 구할 수 없어, 산업용 불량 검출 공개 데이터셋을 설비 카메라 이미지로 가정하여 사용
- 정상 약 229장 (train 약 209 + test 20), 불량 63장 (broken_large 20, broken_small 22, contamination 21)
- 정상이 불량보다 약 3.6배 많은 데이터 불균형이 있어, 데이터 분할과 임계값 조정에 신경 쓸 예정

## 개발 과정
- 2026-10-26: 프로젝트 시작, GitHub 저장소 생성, Colab GPU 환경 확인, 데이터셋 확보, MariaDB 동작 확인

## 진행 계획
- [x]] 데이터 정리 및 정상/불량 분류
- [ ] ResNet18 전이학습
- [ ] 성능 평가 (재현율, F1, 혼동행렬) 및 임계값 조정
- [ ] MariaDB 저장
- [ ] 소켓 서버/클라이언트
- [ ] Streamlit 대시보드


