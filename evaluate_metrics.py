import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

# Định nghĩa tên các lớp
class_names = ['Fall Down', 'Lying Down', 'Sit down', 'Sitting', 'Stand up', 'Standing', 'Walking']

# Ma trận nhầm lẫn từ hình ảnh
confusion_matrix = np.array([
    [8, 2, 0, 0, 0, 0, 0],  # Fall Down
    [0, 9, 0, 0, 0, 1, 0],  # Lying Down
    [1, 0, 6, 3, 0, 0, 0],  # Sit down
    [0, 0, 0, 9, 1, 0, 0],  # Sitting
    [0, 0, 0, 1, 8, 1, 0],  # Stand up
    [0, 0, 0, 0, 0, 7, 3],  # Standing
    [0, 0, 0, 0, 0, 3, 7]   # Walking
])

# Tạo nhãn thực tế và dự đoán
y_true = []
y_pred = []
for i in range(len(confusion_matrix)):
    for j in range(len(confusion_matrix)):
        y_true.extend([i] * confusion_matrix[i][j])
        y_pred.extend([j] * confusion_matrix[i][j])

# Tính toán các metrics cho từng lớp
precisions = precision_score(y_true, y_pred, average=None)
recalls = recall_score(y_true, y_pred, average=None)
f1_scores = f1_score(y_true, y_pred, average=None)

# Tính số lượng mẫu cho mỗi lớp
support = np.sum(confusion_matrix, axis=1)

# In kết quả theo định dạng yêu cầu
print(f"{'':>20} {'precision':>10} {'recall':>10} {'f1-score':>10} {'support':>10}")
print()

for i, class_name in enumerate(class_names):
    print(f"{class_name:>20} {precisions[i]:>10.2f} {recalls[i]:>10.2f} {f1_scores[i]:>10.2f} {support[i]:>10d}")

print()
print(f"{'accuracy':>20} {'':<10} {'':<10} {accuracy_score(y_true, y_pred):>10.2f} {sum(support):>10d}")

# Tính macro avg
macro_precision = np.mean(precisions)
macro_recall = np.mean(recalls)
macro_f1 = np.mean(f1_scores)
print(f"{'macro avg':>20} {macro_precision:>10.2f} {macro_recall:>10.2f} {macro_f1:>10.2f} {sum(support):>10d}")

# Tính weighted avg
weighted_precision = np.average(precisions, weights=support)
weighted_recall = np.average(recalls, weights=support)
weighted_f1 = np.average(f1_scores, weights=support)
print(f"{'weighted avg':>20} {weighted_precision:>10.2f} {weighted_recall:>10.2f} {weighted_f1:>10.2f} {sum(support):>10d}") 