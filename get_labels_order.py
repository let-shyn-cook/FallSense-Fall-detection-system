import os

def get_labels_order(data_dir='data_action/train'):
    # Lấy danh sách các thư mục (nhãn) và sắp xếp theo thứ tự
    labels = sorted(os.listdir(data_dir))
    
    # In thông tin về thứ tự các nhãn
    print("Thứ tự các nhãn:")
    for idx, label in enumerate(labels):
        print(f"{idx}: {label}")
    
    # Lưu thông tin vào file
    with open('label_order.txt', 'w') as f:
        for idx, label in enumerate(labels):
            f.write(f"{idx}: {label}\n")
    
    print("\nĐã lưu thông tin vào file 'label_order.txt'")
    return labels

if __name__ == '__main__':
    labels = get_labels_order()