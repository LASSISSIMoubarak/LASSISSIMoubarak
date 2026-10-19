import json

import pytest

from mlops_breast_cancer import data_utils, predict, train


def test_pipeline_runs_from_generated_data(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    model_dir = tmp_path / "models"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(data_utils, "DATA_DIR", data_dir)
    monkeypatch.setattr(train, "MODEL_DIR", model_dir)
    monkeypatch.setattr(predict, "MODEL_DIR", model_dir)

    data_utils.create_data(test_size=0.2, random_state=42)

    train_data, train_labels, target_names = data_utils.load_train_data()
    test_data, test_labels, _ = data_utils.load_test_data()
    assert train_data.shape == (455, 30)
    assert test_data.shape == (114, 30)
    assert len(train_labels) == 455
    assert len(test_labels) == 114
    assert target_names == ["malignant", "benign"]
    assert json.loads((data_dir / "metadata.json").read_text(encoding="utf-8"))[
        "target_names"
    ] == target_names

    train.train_model(random_state=42)
    predict.predict_example(index=0)

    assert (model_dir / "logistic_regression_model.pkl").is_file()
    assert (model_dir / "standard_scaler.pkl").is_file()
    output = capsys.readouterr().out
    assert "Classification report on test set:" in output
    assert "Predicted label:" in output


def test_prediction_rejects_out_of_range_index(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    model_dir = tmp_path / "models"
    monkeypatch.setattr(data_utils, "DATA_DIR", data_dir)
    monkeypatch.setattr(train, "MODEL_DIR", model_dir)
    monkeypatch.setattr(predict, "MODEL_DIR", model_dir)
    data_utils.create_data(test_size=0.2, random_state=42)
    train.train_model(random_state=42)

    with pytest.raises(IndexError, match="out of range"):
        predict.predict_example(index=114)
