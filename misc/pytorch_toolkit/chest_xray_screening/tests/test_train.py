import unittest
import os
import json
import time
import sys
from torch.utils.data import DataLoader
from google_drive_downloader import GoogleDriveDownloader as gdd
sys.path.append(os.path.abspath('../chest_xray_screening'))
sys.path.append(os.path.abspath('../utils'))
from train import RSNATrainer
from dataloader import RSNADataSet
from model import DenseNet121

def get_config(optimised=False):
    path = os.path.dirname(os.path.realpath(__file__))
    with open(path+'/test_config.json','r') as f1:
        config_file = json.load(f1)
    if optimised:
        config = config_file['train_eff']
    else:
        config = config_file['train']
    return config

def download_checkpoint():
    os.makedirs('model_weights')
    gdd.download_file_from_google_drive(file_id='1z4HuSVXyD59BHhw93j-BVbx6In1HZQn2',
                                    dest_path='model_weights/chest_xray_screening.pth.tar',
                                    unzip=False)
    gdd.download_file_from_google_drive(file_id='1HUmG-wKRoKYxBdwu0_LX1ascBRmA-z5e',
                                    dest_path='model_weights/chest_xray_screening_eff.pth.tar',
                                    unzip=False)

class TrainerTest(unittest.TestCase):
    config = get_config()
    class_count = config["clscount"]
    image_path = '../../../../data/chest_xray_screening/'
    learn_rate = config["lr"]
    tr_list = config["dummy_train_list"]
    val_list = config["dummy_valid_list"]
    test_list = config["dummy_test_list"]
    labels = config["dummy_labels"]

    dataset_train = RSNADataSet(tr_list, labels, image_path, transform=True)
    dataset_valid = RSNADataSet(val_list, labels, image_path, transform=True)
    dataset_test = RSNADataSet(test_list, labels, image_path, transform=True)
    data_loader_train = DataLoader(
        dataset=dataset_train,
        batch_size=2,
        shuffle=True,
        num_workers=4,
        pin_memory=False)
    data_loader_valid = DataLoader(
        dataset=dataset_valid,
        batch_size=2,
        shuffle=False,
        num_workers=4,
        pin_memory=False)
    data_loader_test = DataLoader(
        dataset=dataset_test,
        batch_size=1,
        shuffle=False,
        num_workers=4,
        pin_memory=False)


    def test_config(self):
        self.assertGreaterEqual(self.learn_rate,1e-8)
        self.assertEqual(self.class_count,3)

    def test_trainer(self):
        self.model = DenseNet121(self.class_count)
        self.class_names = self.config["class_names"]
        self.checkpoint = self.config["checkpoint"]
        if not os.path.isdir('model_weights'):
            download_checkpoint()
        self.device = self.config["device"]
        self.trainer = RSNATrainer(
            self.model, self.data_loader_train,
            self.data_loader_valid, self.data_loader_test,
            self.class_count, self.checkpoint,
            self.device, self.class_names,self.learn_rate)
        timestamp_launch = time.strftime("%d%m%Y - %H%M%S")
        self.trainer.train(self.config["max_epoch"], timestamp_launch, self.config["savepath"])
        cur_train_loss = self.trainer.current_train_loss
        cur_valid_loss = self.trainer.current_valid_loss
        self.trainer.train(self.config["max_epoch"], timestamp_launch, self.config["savepath"])
        self.assertLessEqual(self.trainer.current_train_loss, cur_train_loss)
        self.assertLessEqual(self.trainer.current_valid_loss, cur_valid_loss)

    def test_config_eff(self):
        self.config = get_config(optimised=True)
        self.learn_rate = self.config["lr"]
        self.class_count = self.config["clscount"]
        self.assertGreaterEqual(self.learn_rate,1e-8)
        self.assertEqual(self.class_count,3)
        self.assertGreaterEqual(self.config['alpha'],0)
        self.assertGreaterEqual(self.config['phi'],0)
        self.assertLessEqual(self.config['alpha'],2)
        self.assertLessEqual(self.config['phi'],1)


if __name__ == '__main__':

    unittest.main()
