# model.py: 사진 1장을 정상/불량으로 판정하는 함수
import torch, torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image

MODEL_PATH = 'models/best_model.pth'
THRESHOLD = 0.5   # 불량확률이 이 값 이상이면 불량

device = 'cuda' if torch.cuda.is_available() else 'cpu'

# 학습 때와 똑같은 전처리 (다르면 판정이 틀어짐)
_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

def _load_model():
    m = models.resnet18(weights=None)          # 구조만 만들고
    m.fc = nn.Linear(m.fc.in_features, 2)      # 마지막 층을 2개로 교체
    m.load_state_dict(torch.load(MODEL_PATH, map_location=device))  # 학습 결과 불러오기
    return m.to(device).eval()

_model = _load_model()

def predict(image, threshold=THRESHOLD):
    """image: 파일 경로 또는 PIL 이미지 -> {'label', 'defect_prob'}"""
    img = Image.open(image) if isinstance(image, str) else image
    x = _tf(img.convert('RGB')).unsqueeze(0).to(device)
    with torch.no_grad():
        defect_prob = F.softmax(_model(x), dim=1)[0][0].item()   # 0번 = defect
    label = '불량' if defect_prob >= threshold else '정상'
    return {'label': label, 'defect_prob': round(defect_prob, 4)}
