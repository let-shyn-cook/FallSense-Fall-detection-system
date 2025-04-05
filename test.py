import torch
import pickle
from torch.utils.data import DataLoader, TensorDataset
# import model deep learning
from models.stgcn import *
import numpy as np
from sklearn import metrics
from util.plot import plot_cm
from tqdm import tqdm
from dataloader.dataset import processing_data


def detect_image(path_test, path_model, batch_size=256):

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    # load model
    class_names = ['Fall Down', 'Lying Down', 'Sit down', 'Sitting', 'Stand up', 'Standing', 'Walking']
    # class_names = ['Other action', 'Fall Down']
    # class_names = ['Siting', 'Lying Down', 'Walking or Standing', 'Fall Down']
    # graph_args = {'strategy': 'spatial', 'layout': 'coco_cut'}
    graph_args = {'strategy': 'spatial'}
    model = TwoStreamSpatialTemporalGraph(graph_args, len(class_names)).to(device)
    model.load_state_dict(torch.load(path_model, map_location=device))
    model.to(device=device)
    model.eval()

    # Load dataset
    features, labels = [], []
    with open(path_test, 'rb') as f:
        fts, lbs = pickle.load(f)
        features.append(fts)
        labels.append(lbs)
    del fts, lbs

    features = np.concatenate(features, axis=0)  # 30x34
    # get 15 frame
    features = features[:, ::2, :, :]
    # add point center with yolov3
    # features = np.concatenate((features, np.expand_dims((features[:, :, 1, :] + features[:, :, 1, :]) / 2, axis=2)),
    #                           axis=2)
    features[:, :, :, :2] = processing_data(features[:, :, :, :2])
    labels = np.concatenate(labels, axis=0).argmax(1)

    print(" --------- Number class test ---------")
    for i in range(7):
        print(f"class {i}: {labels.tolist().count(i)}")

    test_dataset = TensorDataset(torch.tensor(features, dtype=torch.float32).permute(0, 3, 1, 2),
                                torch.tensor(labels, dtype=torch.float32))

    test_loader = DataLoader(
        test_dataset,
        batch_size=32, shuffle=False,
        num_workers=4, pin_memory=True)
    truth = []
    pred = []
    pbar_test = tqdm(test_loader, desc=f'Evaluate', unit='batch')
    for batch_vid, labels in pbar_test:
        # Giải phóng bộ nhớ cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        mot = batch_vid[:, :2, 1:, :] - batch_vid[:, :2, :-1, :]
        mot, batch_vid, labels = mot.to(device), batch_vid.to(device), labels.to(device)
        outputs = model((batch_vid, mot))
        _, preds = torch.max(outputs, 1)
        truth.extend(labels.cpu().data.tolist())
        pred.extend(preds.cpu().tolist())
        
        # Giải phóng bộ nhớ GPU
        del mot, batch_vid, labels, outputs, preds
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
    CM = metrics.confusion_matrix(truth, pred).T
    precision = metrics.precision_score(truth, pred, average=None)
    recall = metrics.recall_score(truth, pred, average=None)
    accuracy = metrics.accuracy_score(truth, pred, normalize=True)
    f1_score = metrics.f1_score(truth, pred, average=None)
    print("Accuracy: ", round(accuracy, 2) * 100)
    for i in range(len(class_names)):
        print('****Precision-Recall-F1-Score of class {}****'.format(class_names[i]))
        print('Precision: ', precision[i])
        print('Recall: ', recall[i])
        print('F1-score', f1_score[i])
    with open('info_stgcn/info_stgcn.txt', 'w') as file:
        file.write('{} {} {}'.format(precision, recall, f1_score))
    plot_cm(CM, normalize=False, save_dir='info_stgcn', names_x=class_names,
            names_y=class_names, show=False)
    print('Finishing!.')


if __name__ == '__main__':
    path_model = r'runs\best.pt'
    path_frame = 'test.pkl'
    detect_image(path_frame, path_model, batch_size=64)
