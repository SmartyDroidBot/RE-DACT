import os, shutil, json
import numpy as np
import pandas as pd
import torch
from .db_service import getDBDataframe
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from torch.utils.data import Dataset
from django.conf import settings

def train_model():
    # Parameters
    TRAIN_EPOCHS = 1
    LEARNING_RATE = 2e-5
    TRAIN_BATCH_SIZE = 4
    VALID_BATCH_SIZE = 4

    # Clear model checkpoint
    clear_model_checkpoint()

    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(settings.MODEL_PATH)
    label2id = model.config.label2id

    # Load data
    data = getDBDataframe()

    # Split data
    y = data.pop('label')
    X = data.pop('word')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

    # Create dataloaders
    train_dataset = CustomDataset(X_train, y_train, tokenizer, label2id)
    test_dataset = CustomDataset(X_test, y_test, tokenizer, label2id)

    args = TrainingArguments(
        output_dir=settings.MODEL_PATH,
        evaluation_strategy = 'epoch',
        save_strategy = 'epoch',
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=TRAIN_BATCH_SIZE,
        per_device_eval_batch_size=VALID_BATCH_SIZE,
        num_train_epochs=TRAIN_EPOCHS,
        save_total_limit=1,
        push_to_hub=False,
        report_to='none' # Disable wandb logging
    )

    # Define a metric
    def compute_metrics(p):
        predictions, labels = p.predictions, p.label_ids
        predictions = np.argmax(predictions, axis=1)
        
        # Calculate accuracy
        accuracy = accuracy_score(labels, predictions)

        return {"accuracy": accuracy}

    # Create a trainer
    trainer = Trainer(
        model,
        args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics
    )

    train_output = trainer.train() # Training
    append_logs_to_file(settings.MODEL_TRAINING_LOGS, train_output.metrics)

    del tokenizer, model, trainer
    move_checkpoint_to_models()

    return train_output.metrics
    
# Clears previous model training checkpoint
def clear_model_checkpoint():
    for folder in os.listdir(settings.MODEL_PATH):
        folder_path = os.path.join(settings.MODEL_PATH, folder)
        if os.path.isdir(folder_path) and folder.startswith('checkpoint'):
            # Remove the directory and its contents
            shutil.rmtree(folder_path)
            print(f"Removed checkpoint folder: {folder_path}")

# Appends logs to a json file
def append_logs_to_file(log_file_path, new_logs):
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as file:
            try:
                existing_logs = json.load(file)
            except json.JSONDecodeError:
                existing_logs = []
    else:
        existing_logs = []

    existing_logs.append(new_logs)
    with open(log_file_path, 'w') as file:
        json.dump(existing_logs, file, indent=4)

    print(f"Logs appended to {log_file_path}")

# Move checkpoint folder to models directory
def move_checkpoint_to_models():
    for folder in os.listdir(settings.MODEL_PATH):
        folder_path = os.path.join(settings.MODEL_PATH, folder)
        if os.path.isdir(folder_path) and folder.startswith('checkpoint'):
            for item in os.listdir(folder_path):
                source_path = os.path.join(folder_path, item)
                target_path = os.path.join(settings.MODEL_PATH, item)

                # Move the file or folder to the model path
                if os.path.isfile(source_path) or os.path.islink(source_path):
                    shutil.move(source_path, target_path)
                elif os.path.isdir(source_path):
                    shutil.move(source_path, target_path)

            print(f"All checkpoint model files moved to MODEL_PATH.")


# Custom Dataset class for training
class CustomDataset(Dataset):
    def __init__(self, X, y, tokenizer, label2id):
        self.label2id = label2id        
        self.examples = []

        for input, label in zip(X.values, y.values):
            input = tokenizer.encode_plus(input, max_length=512, truncation=True, padding='max_length', return_tensors='pt')
            self.examples.append({'input_ids': input['input_ids'].squeeze(),
                                  'attention_mask': input['attention_mask'].squeeze(),
                                  'labels' : torch.tensor(self.get_id(label), dtype=torch.long)})
    
    def get_id(self, label):
        for key, value in self.label2id.items():
            if label == key:
                return value

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, i):
        return self.examples[i]
