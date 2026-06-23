import logging
import os
import sys

import numpy as np
from sklearn.model_selection import train_test_split

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")
from shared.mongo import mongo_client  # noqa

logger = logging.getLogger(__name__)
mongo = mongo_client()


def get_finetuning_data(min_reliable: int, min_misinfo: int) -> tuple[list, list]:
    """Fetch labeled posts from MongoDB for fine-tuning.

    Uses normalized_text (clean but semantically intact) as input.
    Label 1 = reliable source, 0 = misinformation category.
    """
    collection = mongo.use_collection("cleaned_posts")

    reliable = list(
        collection.find(
            {
                "source_label": "reliable",
                "normalized_text": {"$exists": True, "$ne": ""},
            },
            {"normalized_text": 1},
        )
    )
    misinfo = list(
        collection.find(
            {
                "category": "Misinformation",
                "normalized_text": {"$exists": True, "$ne": ""},
            },
            {"normalized_text": 1},
        )
    )

    if len(reliable) < min_reliable:
        raise ValueError(
            f"Not enough reliable posts: {len(reliable)} found, need {min_reliable}. "
            "Run ingest_from_bluesky + nlp_transform first."
        )
    if len(misinfo) < min_misinfo:
        raise ValueError(
            f"Not enough misinformation posts: {len(misinfo)} found, need {min_misinfo}. "
            "Run ingest_from_bluesky + nlp_transform first."
        )

    texts = [p["normalized_text"] for p in reliable] + [
        p["normalized_text"] for p in misinfo
    ]
    labels = [1] * len(reliable) + [0] * len(misinfo)

    logger.info(
        f"Fine-tuning data: {len(reliable)} reliable (label=1), {len(misinfo)} misinfo (label=0)"
    )
    return texts, labels


def finetune_xlm_roberta(
    texts: list,
    labels: list,
    model_name: str,
    max_length: int,
    batch_size: int,
    num_epochs: int,
    learning_rate: float,
    unfreeze_layers: list,
    model_path: str,
) -> str:
    """Fine-tune xlm-roberta-base on labeled Bluesky posts.

    Freezes all layers except the last two encoder layers and the classifier head
    to avoid overfitting on small corpora. Saves HuggingFace model to model_path.
    """
    import torch  # noqa: PLC0415
    from torch.utils.data import Dataset  # noqa: PLC0415
    from transformers import (  # noqa: PLC0415
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

    # Freeze all params, then selectively unfreeze
    for param in model.parameters():
        param.requires_grad = False
    for name, param in model.named_parameters():
        if any(layer in name for layer in unfreeze_layers):
            param.requires_grad = True

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    logger.info(
        f"Trainable params: {trainable:,} / {total:,} ({trainable / total:.1%})"
    )

    # 80/20 train/val split
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    class PostDataset(Dataset):
        def __init__(self, texts, labels):
            self.enc = tokenizer(
                texts,
                truncation=True,
                padding=True,
                max_length=max_length,
                return_tensors="pt",
            )
            self.labels = labels

        def __len__(self):
            return len(self.labels)

        def __getitem__(self, idx):
            item = {k: v[idx] for k, v in self.enc.items()}
            item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
            return item

    train_ds = PostDataset(train_texts, train_labels)
    val_ds = PostDataset(val_texts, val_labels)

    def compute_metrics(eval_pred):
        from sklearn.metrics import roc_auc_score  # noqa: PLC0415

        logits, labels = eval_pred
        probs = torch.softmax(torch.tensor(logits), dim=-1)[:, 1].numpy()
        try:
            auc = roc_auc_score(labels, probs)
        except ValueError:
            auc = 0.0
        preds = (probs >= 0.5).astype(int)  # noqa: PLR2004
        acc = float(np.mean(preds == labels))
        return {"roc_auc": round(auc, 4), "accuracy": round(acc, 4)}

    args = TrainingArguments(
        output_dir=model_path,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="roc_auc",
        logging_steps=10,
        use_cpu=not torch.cuda.is_available(),
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    model.save_pretrained(model_path)
    tokenizer.save_pretrained(model_path)
    logger.info(f"Fine-tuned model saved to {model_path}")
    return model_path
