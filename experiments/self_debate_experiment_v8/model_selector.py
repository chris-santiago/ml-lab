import json
import random


def fetch(path):
    with open(path, "r") as fp:
        models = json.load(fp)["models"]
        return {
            item["index"]: {k: v for k, v in item.items() if k != "index"}
            for item in models
        }


def generate_models(models: dict, n: int = 3):
    idx = random.sample(range(len(models)), N)
    yield [models[i]["model_id"] for i in idx]


if __name__ == "__main__":
    PATH = "/Users/chrissantiago/Dropbox/GitHub/ml-lab/experiments/self_debate_experiment_v8/models.json"
    N = 3
    models = fetch(PATH)
    print(next(generate_models(models, N)))
