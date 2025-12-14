import torch.nn as nn
import numpy as np
import torch
from tqdm import tqdm
import mlflow
from item import BaseOptimizerConfig, BaseSchedulerConfig, AdamConfig, ReduceLROnPlateauConfig
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve, ConfusionMatrixDisplay, accuracy_score

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import json
import os
import dataloader as dl
##### HYPERPARAMETERS #####
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
dir="/runtime/data/save_of_weigths"
os.makedirs(dir,exist_ok=True)

class MLP(nn.Module):
    """
    MLP Definiation as taken from the paper of Romaric
    """
    def __init__(self, input_features, growth_rate):
        super(MLP, self).__init__()
        self.block1 = nn.Sequential(
            nn.Linear(input_features, growth_rate),
            nn.ReLU(),
        )
        self.block2 = nn.Sequential(
            nn.Linear(growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.block3 = nn.Sequential(
            nn.Linear(2 * growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.block4 = nn.Sequential(
            nn.Linear(3 * growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.block5 = nn.Sequential(
            nn.Linear(4 * growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.block6 = nn.Sequential(
            nn.Linear(5 * growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.output = nn.Linear(growth_rate, 1)

    def forward(self, x):
        x1 = self.block1(x)
        x2 = self.block2(x1)
        x3 = self.block3(torch.cat([x1, x2], dim=1))
        x4 = self.block4(torch.cat([x1, x2, x3], dim=1))
        x5 = self.block5(torch.cat([x1, x2, x3, x4], dim=1))
        x6 = self.block6(torch.cat([x1, x2, x3, x4, x5], dim=1))
        y = self.output(x3)
        y = torch.sigmoid(y)
        return y


class MLPWrapper:
    
    def __init__(self, *, input_features, train_loader, test_loader, model_seed, device, 
             growth_rate, epochs, criterion, optimizer_config, scheduler_config,data_seed):

        
        # Make a dictionnary for guarden metrics
        self.train_metrics = {
            'loss': [], 'accuracy': [], 
            'pos_precision': [], 'neg_precision': [],
            'loss_pos':[],'loss_neg':[]
        }

        self.test_metrics = {
            'loss': [], 'accuracy': [], 
            'pos_precision': [], 'neg_precision': [],
            'loss_pos':[],'loss_neg':[]
        }
        
       
        # Parameters of object
        self.input_features = input_features
        self.growth_rate = growth_rate
        self.train_loader = train_loader
        self.test_loader = test_loader
        self.model_seed = model_seed
        self.epochs = epochs
        self.device = device
        self.data_seed=data_seed
        self.model_test_performance=[]
        self.model_train_performance=[]
        self.learning=[]

        # Initialize model
        torch.manual_seed(model_seed)
        self.model = MLP(input_features=input_features, growth_rate=growth_rate).to(device)
        
        # Optimization configure
        self.criterion = criterion
        self.optimizer = self.init_optimizer(optimizer_config) 
        self.scheduler = self.init_scheduler(scheduler_config)

  

    def init_optimizer(self, optimizer_config):
        return AdamConfig(self.model.parameters(), **optimizer_config).create_optimizer()

    def init_scheduler(self, scheduler_config):
        return ReduceLROnPlateauConfig(**scheduler_config).create_scheduler(self.optimizer)

    def compute_count_prediction(self, targets, predictions):
        """To calcul out prediction of model for confusion matrix"""
        tp = ((targets == 1) & (predictions == 1)).sum()
        tn = ((targets == 0) & (predictions == 0)).sum()
        fp = ((targets == 1) & (predictions == 0)).sum()
        fn = ((targets == 0) & (predictions == 1)).sum()
        
        return {'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn}

    def calculate_metric(self, counts):
        """Calcule les métriques avancées à partir des comptes"""
        tp = counts['tp']
        tn = counts['tn']
        fp = counts['fp']
        fn = counts['fn']
        
        total = tp + tn + fp + fn
        accuracy = 100 * (tp + tn) / (total )
        pos_precision = 100 * tp / (tp + fp)
        neg_precision = 100 * tn / (tn + fn)
        
        return {
            'accuracy': accuracy,
            'pos_precision': pos_precision,
            'neg_precision': neg_precision
        }
    
  
    def train(self,int_to_id_,int_to_id,mode_=None):
        """Training_model
        do not forget the two mode and mode_ in evaluate and train and evaluate , use evaluate=='Full_Test'
        to evaluate full data and None for train and test"""
        for epoch in range(self.epochs):
            train_metrics = self.train_by_epoch(epoch,int_to_id_)
            if mode_=='train_and_test':
                test_metrics=self.evaluate(self.test_loader,int_to_id,evaluate=None,mode='train_and_test')
                df_results_train=None
                df_results_test=None
                print(test_metrics)
                mlflow.log_dict(test_metrics,f'total_test_for_matrix_confusion{self.model_seed}_{self.data_seed}.json')
                mlflow.log_dict(train_metrics,f'total_train_for_matrix_confusion{self.model_seed}_{self.data_seed}.json')
                conf_matrix = np.array([[test_metrics['tp'], test_metrics['fp']],
                        [test_metrics['fn'], test_metrics['tn']]])
                # Création du heatmap
                fig=plt.figure(figsize=(6,4))
                sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues",
                            xticklabels=["Prédit Positif", "Prédit Négatif"],
                            yticklabels=["Réel Positif", "Réel Négatif"])
                plt.title("Matrice de confusion")
                plt.xlabel("Valeurs prédites")
                plt.ylabel("Valeurs réelles")
                mlflow.log_figure(fig,f'confusion_matrix_{self.model_seed}_{self.data_seed}_.png')
            else :
                df_results_test,test_metrics=self.evaluate(self.test_loader,int_to_id,evaluate='Full_Test',mode=None)
                self.model_train=None
                self.model_test=None
   
            if epoch == self.epochs - 1:
                weigths_saves=os.path.join(dir,f"checkpoint_V901_{self.model_seed}_{self.data_seed}_{epoch}.pth")
                self.save_checkpoint(f"{weigths_saves}")


            ###################################################################################
            self.scheduler.step(self.model_test_per_by_epoch['losses'])
            ########################################################
            self.learning.append(self.optimizer.param_groups[0]['lr'])
            print(f"Learning rate: {self.optimizer.param_groups[0]['lr']}")
            print(self.model_train_per_by_epoch['losses'])
           
        self.model_train=pd.DataFrame(self.model_train_performance)
        self.model_test=pd.DataFrame(self.model_test_performance)
        print(f'train_metric== {self.model_train}')
        print(f'test_metric=={self.model_test}')
        return df_results_train,df_results_test, self.model_train, self.model_test

    def train_by_epoch(self, epoch,int_to_id_):
        """Train_epoch by epoch"""
        self.model.train()
        # Initialisation
        total_loss_train = 0
        total_loss_train_neg=0
        total_loss_train_pos=0
        total_batch=0
        total_batch_pos=0
        total_batch_neg=0
        results_train = {
            'preds': [], 'targets': [], 'indices': [], 'outputs': [],
            'losses': [], 'losses_pos': [], 'losses_neg': []
        }
        metrics_train= {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0}
        

        with tqdm(self.train_loader, unit="batch") as t:
            t.set_description(f"Epoch {epoch}")
            
            for data, target,index in t:
                data, target = data.to(self.device), target.to(self.device)
                self.optimizer.zero_grad()
                # Forward-backward pass
                output = self.model(data.float())
                
                # Conversion des index
                batch_indices = [int_to_id_[idx.item()] for idx in index]
                
                # Stockage des résultats
                batch_size = target.size(0)
                results_train['outputs'].extend(output.cpu().detach().numpy())
                results_train['targets'].append(target.cpu().numpy())
                results_train['indices'].append(np.array(batch_indices))
                
                # Calcul des prédictions
                preds =  np.where(output.data > 0.5, 1, 0).reshape(
                        1, len(output)
                    )[0]

                results_train['preds'].append(preds)
                masq_pos=(target == 1).view(-1)
                masq_neg=(target == 0).view(-1)
                # Calcul des métriques
                batch_metrics = self.compute_count_prediction(target.cpu().numpy(), preds)
                for k in metrics_train:
                    metrics_train[k] += batch_metrics[k]
                
                # Calcul des losses
                loss = self.criterion(output, target.float().view(-1, 1))
                loss.backward()
                self.optimizer.step()
                total_loss_train += loss.item()    
                total_batch+=1
                loss_neg= self.criterion(output[masq_neg], target[masq_neg].float().view(-1, 1))
                total_loss_train_neg+=np.nan_to_num(loss_neg.item()) 
                total_batch_neg+=1
                loss_pos= self.criterion(output[masq_pos], target[masq_pos].float().view(-1, 1))
                total_loss_train_pos+=np.nan_to_num(loss_pos.item()) 
                total_batch_pos+=1
                t.set_postfix(loss=f"{loss.item():.4f}")
        #Train metrics
        self.model_train_per_by_epoch=self.calculate_metric(metrics_train)
        total_loss_=total_loss_train/total_batch
        total_loss_Neg_=total_loss_train_neg/total_batch_neg
        total_loss_Pos_=total_loss_train_pos/total_batch_pos
        self.model_train_per_by_epoch['losses']=total_loss_
        self.model_train_per_by_epoch['losses_neg']=total_loss_Neg_
        self.model_train_per_by_epoch['losses_pos']=total_loss_Pos_
        self.model_train_performance.append(self.model_train_per_by_epoch)
        return  metrics_train

    def evaluate(self, loader, int_to_id,evaluate=None,mode=None):
        self.model.eval()
        # Initialisation
        total_loss_test = 0
        total_loss_test_neg=0
        total_loss_test_pos=0
        total_batch=0
        total_batch_pos=0
        total_batch_neg=0
        total_loss_Pos_=0
        results_test = {
            'preds': [], 'targets': [], 'indices': [], 'outputs': [],
            'losses': [], 'losses_pos': [], 'losses_neg': []
        }
        metrics_test = {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0}

        with torch.no_grad():
            for data, target, index in loader:
                # Forward pass
                data, target = data.to(self.device), target.to(self.device)
                output = self.model(data.float())
                # Conversion des index
                batch_indices = [int_to_id[idx.item()] for idx in index]
                
                # Stockage des résultats
                batch_size = target.size(0)
                results_test['outputs'].extend(output.cpu().numpy())
                results_test['targets'].append(target.cpu().numpy())
                results_test['indices'].append(np.array(batch_indices))
                
                # Calcul des prédictions
                preds =  np.where(output.data > 0.5, 1, 0).reshape(
                        1, len(output)
                    )[0]

                results_test['preds'].append(preds)

                masq_pos=(target == 1).view(-1)
                masq_neg=(target == 0).view(-1)
                # Calcul des métriques
                batch_metrics = self.compute_count_prediction(target.cpu().numpy(), preds)
                for k in metrics_test:
                    metrics_test[k] += batch_metrics[k]
                if evaluate=='Full_Test':
                    loss = self.criterion(output, target.float().view(-1, 1)).detach().flatten().tolist()
                    results_test['losses'].append(loss)
                    loss_neg= self.criterion(output[masq_neg], target[masq_neg].float().view(-1, 1)).flatten().tolist()
                    losses_neg = np.full(batch_size, np.nan)
                    losses_neg[masq_neg] = loss_neg
                    results_test['losses_neg'].append(losses_neg)
                    loss_pos= self.criterion(output[masq_pos], target[masq_pos].float().view(-1, 1)).flatten().tolist()
                    losses_pos = np.full(batch_size, np.nan)  
                    losses_pos[masq_pos] = loss_pos
                    results_test['losses_pos'].append(losses_pos)
                else:
                    # Calcul des losses
                    loss = self.criterion(output, target.float().view(-1, 1))
                    total_loss_test += loss.item() 
                    total_batch+=1
                    loss_neg= self.criterion(output[masq_neg], target[masq_neg].float().view(-1, 1))
                    total_loss_test_neg +=np.nan_to_num(loss_neg.item()) 
                    total_batch_neg +=1
                    loss_pos= self.criterion(output[masq_pos], target[masq_pos].float().view(-1, 1))  
                    total_loss_test_pos += np.nan_to_num(loss_pos.item()) 
                    total_batch_pos+=1
        if mode=='train_and_test':
            #les preformances du jeu test 
            self.model_test_per_by_epoch=self.calculate_metric(metrics_test)
            total_loss_=(total_loss_test)/(len(loader))
            total_loss_Neg_=total_loss_test_neg/total_batch_neg
            total_loss_Pos_=(total_loss_test_pos)/(total_batch_pos)
            self.model_test_per_by_epoch['losses']=total_loss_
            self.model_test_per_by_epoch['losses_neg']=total_loss_Neg_
            self.model_test_per_by_epoch['losses_pos']=total_loss_Pos_
            self.model_test_performance.append(self.model_test_per_by_epoch)
            return metrics_test
        else:
            self.model_test_per_by_epoch=self.calculate_metric(metrics_test)
            final_results_test = {
            'outputs': np.concatenate(results_test['outputs']),
            'targets': np.concatenate(results_test['targets']),
            'indices': np.concatenate(results_test['indices']),
            'losses': np.concatenate(results_test['losses']),
            'preds':np.concatenate(results_test['preds']) ,
            'losses_neg':np.concatenate(results_test['losses_neg']),
            'losses_pos':np.concatenate(results_test['losses_pos'])
                }
        # Création du DataFrame
            df_results = pd.DataFrame({
            'index': final_results_test['indices'],
            'target': final_results_test['targets'],
            'output': final_results_test['outputs'],
            'preds': final_results_test['preds'],
            'losses':final_results_test['losses'],
            'losses_neg':final_results_test['losses_neg'],
            'losses_pos':final_results_test['losses_pos']
            })
            print(self.model_test_per_by_epoch)
            return df_results,metrics_test
    
    def mlflow_log_metrics(self, train_metrics, test_metrics, epoch):
        """Logging  métriques in  MLflow """
        # Logging MLflow
        for name, value in train_metrics.items():
            mlflow.log_metric(f"train_{name}", value, step=epoch)
            mlflow.log_dict(self.train_metrics, "train_metrics.json")

        for name, value in test_metrics.items():
            mlflow.log_metric(f"test_{name}", value, step=epoch)
            mlflow.log_dict(self.test_metrics, "test_metrics.json")
        
        # Affichage console
        print(f"\nEpoch {epoch}:")
        print(f"Train - Loss: {train_metrics['loss']:.4f}, Acc: {train_metrics['accuracy']:.2f}%")
        print(f"Test  - Loss: {test_metrics['loss']:.4f}, Acc: {test_metrics['accuracy']:.2f}%")

    def save_checkpoint(self, path):
            """
            Sauvegarde le modèle et crée automatiquement le dossier si besoin
            
            Args:
                path: Chemin du fichier de checkpoint (.pth)
            """
            torch.save(self.model.state_dict(), path)
          
    def load_model_from_checkpoint(self, path):
        """Charge un modèle à partir d'un checkpoint"""
        self.model.load_state_dict(torch.load(path))
        self.model.to(self.device)


    def plot_metrics(self,fontsize):
        metrics = ['accuracy', 'pos_precision', 'neg_precision']
        metrics_path = f"Metrics_over_epochs_seed_{self.model_seed}_{self.data_seed}.png"
        fig, axes = plt.subplots(1, 3,figsize=(14,4))
        axes = axes.flatten()
        for  metric in metrics:
            ax = axes[0]
            if metric == 'accuracy':
                train_values = self.model_train[metric]
                test_values = self.model_test[metric]
                ax.plot(train_values, label=f'Accuracy train',color='black',linewidth=2)
                ax.plot(test_values, label=f'Accuracy test',color='black',linestyle='dotted',linewidth=2)
            if metric == 'pos_precision':
                train_values = self.model_train[metric]
                test_values =  self.model_test[metric]
                ax.plot(train_values, label=f'PVA train',color='blue',linewidth=2)
                ax.plot(test_values, label=f'PVA test',color='blue',linestyle='dotted',linewidth=2)
            if metric == 'neg_precision':
                train_values = self.model_train[metric]
                test_values =  self.model_test[metric]
                ax.plot(train_values, label=f'PFA train',color='red',linewidth=2)
                ax.plot(test_values, label=f'PFA test',color='red',linestyle='dotted',linewidth=2)
            ax.set_title(f'Metrics over epochs',fontsize=fontsize)
            ax.set_ylim(40, 100)
            ax.set_xlabel('Epochs',fontsize=fontsize) 
            ax.set_ylabel('Percentages',fontsize=fontsize)
            ax.tick_params(axis='both',which='major',labelsize=fontsize+1)
            ax.legend(loc='best',fontsize=fontsize)
            ax.grid(0.3)
        ax = axes[1]
        ax.plot(self.model_train['losses_pos'], label='LVA TRAIN', color='blue',linewidth=2)
        ax.plot( self.model_train['losses_neg'], label='LFA TRAIN', color='red',linewidth=2)
        ax.plot( self.model_test['losses_pos'], label='LVA TEST', color='blue', linestyle='dotted',linewidth=2)
        ax.plot( self.model_test['losses_neg'], label='LFA TEST', color='red', linestyle='dotted',linewidth=2)
        ax.plot( self.model_train['losses'], label='LG TRAIN', color='black',linewidth=2)
        ax.plot( self.model_test['losses'], label='LG TEST', color='black', linestyle='dotted',linewidth=2)
        ax.set_title('Loss over epochs',fontsize=fontsize)
        ax.set_xlabel('Epochs',fontsize=fontsize)
        ax.set_ylabel('Loss',fontsize=fontsize)
        ax.set_ylim(0, 1)
        ax.tick_params(axis='both',which='major',labelsize=fontsize+1)
        ax.legend(loc='best',fontsize=fontsize)
        ax.grid(0.3)
        ax= axes[2]
        ax.plot( self.learning, label='Learning', color='black', linestyle='--',linewidth=2)
        ax.set_title('Learning rate evolution',fontsize=fontsize)
        ax.set_xlabel('Epochs',fontsize=fontsize)
        ax.set_yscale('log')
        # ax.set_ylabel('Valeurs de learning rate',fontsize=fontsize)
        # ax.legend(loc='best',fontsize=fontsize)
        ax.grid(0.3)
        plt.tight_layout()
        plt.tick_params(axis='both',which='major',labelsize=fontsize+1)
        plt.close(fig)
        mlflow.log_figure(fig,metrics_path)

#################################################################################################  Autres Architectures





##################################################################################################################################################







####################################################################################################################################################



class MLPTempSal(nn.Module):
    def __init__(self, temp_input_dim, sal_input_dim, growth_rate):
        super(MLPTempSal, self).__init__()
        self.temp_input_dim = temp_input_dim  
        self.sal_input_dim = sal_input_dim   
        
        self.temp_branch = nn.Sequential(
            nn.Linear(temp_input_dim, growth_rate),
            nn.ReLU(),
            nn.Linear(growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.sal_branch = nn.Sequential(
            nn.Linear(sal_input_dim, growth_rate),
            nn.ReLU(),
            nn.Linear(growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.concat_block = nn.Sequential(
            nn.Linear(2 * growth_rate, growth_rate),
            nn.ReLU(),
            nn.Linear(growth_rate, 1),
        )

    def forward(self, x): 
        x_temp = x[:, :self.temp_input_dim]   
        x_sal = x[:, self.temp_input_dim : self.temp_input_dim + self.sal_input_dim]
        temp_out = self.temp_branch(x_temp)
        sal_out = self.sal_branch(x_sal)
        concat = torch.cat([temp_out, sal_out], dim=1)
        y = self.concat_block(concat)
        return torch.sigmoid(y)








################
class MLPn(nn.Module):
    def __init__(self, input_features, growth_rate):
        super(MLPn, self).__init__()
        self.block1 = nn.Sequential(
            nn.Linear(input_features, growth_rate),
            nn.ReLU(),
        )
        self.block2 = nn.Sequential(
            nn.Linear(growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.block3 = nn.Sequential(
            nn.Linear(2 * growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.block4 = nn.Sequential(
            nn.Linear(3 * growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.block5 = nn.Sequential(
            nn.Linear(4 * growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.block6 = nn.Sequential(
            nn.Linear(5 * growth_rate, growth_rate),
            nn.ReLU(),
        )
        self.output = nn.Linear(growth_rate, 1)

        # Initialisation des poids
        self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        x1 = self.block1(x)
        x2 = self.block2(x1)
        x3 = self.block3(torch.cat([x1, x2], dim=1))
        x4 = self.block4(torch.cat([x1, x2, x3], dim=1))
        x5 = self.block5(torch.cat([x1, x2, x3, x4], dim=1))
        x6 = self.block6(torch.cat([x1, x2, x3, x4, x5], dim=1))
        y = self.output(x3)
        y = torch.sigmoid(y)
        return y
