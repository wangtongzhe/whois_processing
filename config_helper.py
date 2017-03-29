import yaml
import os


class ConfigHelper(object):
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

    @classmethod
    def rabbit_conn_url(cls):
        with open(cls.config_path, "r", encoding="utf-8") as config:
            config_dict = yaml.load(config)
            return config_dict["RabbitMQConnUrl"]

    @classmethod
    def rabbit_task_queue(cls):
        with open(cls.config_path, "r", encoding="utf-8") as config:
            config_dict = yaml.load(config)
            return config_dict["RabbitMQTaskQueue"]

    @classmethod
    def rabbit_result_key(cls):
        with open(cls.config_path, "r", encoding="utf-8") as config:
            config_dict = yaml.load(config)
            return config_dict["RabbitMQResultKey"]
