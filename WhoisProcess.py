import pika
import ThirdPart.whois as whois
import json
import time
import hashlib
from model.whois_item import *
from config_helper import *


params = pika.URLParameters(ConfigHelper.rabbit_conn_url())


def get_whois_info(domain):
    # 初始化信息
    if "." not in domain:
        return None
    obj_item = WhoisItem(domain, domain[domain.rindex(".") + 1:])
    try:
        w_item = whois.whois(domain)
        obj_item.source = w_item.text
        trans_obj = {}
        # 域名注册商
        trans_obj["registrar"] = w_item.get("registrar", "")

        # 注册人名称
        if "name" in w_item.keys():
            trans_obj["name"] = w_item.get("name", "")
        elif "registrant_name" in w_item.keys():
            trans_obj["name"] = w_item.get("registrant_name", "")
        else:
            trans_obj["name"] = ""

        # 注册人电话
        if "phone" in w_item.keys():
            trans_obj["phone"] = "".join(filter(str.isdigit, w_item.get("phone", "")))
        elif "registrant_phone_number" in w_item.keys():
            trans_obj["phone"] = "".join(filter(str.isdigit, w_item.get("registrant_phone_number", "")))
        else:
            trans_obj["phone"] = ""

        # 注册人邮箱
        if "registrant_email" in w_item.keys():
            trans_obj["email"] = w_item.get("registrant_email", "")
        elif "emails" in w_item.keys():
            temp_emails = w_item["emails"]
            if isinstance(temp_emails, list):
                trans_obj["email"] = w_item["emails"][0]
            else:
                trans_obj["email"] = temp_emails
        else:
            trans_obj["email"] = ""

        # 注册地址
        if "address" in w_item.keys():
            if isinstance(w_item.get("address", ""), list):
                trans_obj["address"] = w_item.get("address", "")[0]
            else:
                trans_obj["address"] = w_item.get("address", "")
        elif "registrant_address1" in w_item.keys():
            if isinstance(w_item.get("registrant_address1", ""), list):
                trans_obj["address"] = w_item.get("registrant_address1", "")[0]
            else:
                trans_obj["address"] = w_item.get("registrant_address1", "")
        else:
            trans_obj["address"] = ""

        # dns
        if w_item.get("name_servers", None) is None:
            trans_obj["dns"] = None
        else:
            dns_list = w_item.get("name_servers", [])
            dns_list.sort()
            trans_obj["dns"] = tuple(dns_list)

        # 更新时间
        if "updated_date" in w_item.keys():
            temp_update = w_item.get("updated_date", "")
            if isinstance(temp_update, list):
                trans_obj["updated_time"] = str(temp_update[0])
            else:
                trans_obj["updated_time"] = str(temp_update)
        else:
            trans_obj["updated_time"] = None

        # 创建时间
        if "creation_date" in w_item.keys():
            temp_create = w_item.get("creation_date", "")
            if isinstance(temp_create, list):
                trans_obj["creation_time"] = str(temp_create[0])
            else:
                trans_obj["creation_time"] = str(temp_create)
        else:
            trans_obj["creation_time"] = None

        # 过期时间
        if "expiration_date" in w_item.keys():
            temp_expir = w_item.get("expiration_date", "")
            if isinstance(temp_expir, list):
                trans_obj["expiration_time"] = str(temp_expir[0])
            else:
                trans_obj["expiration_time"] = str(temp_expir)
        else:
            trans_obj["expiration_time"] = None
        obj_item.trans_obj = trans_obj
        obj_item.trans_sha256 = hashlib.sha256(
            str.encode(json.dumps(trans_obj, sort_keys=True), encoding='utf-8')).hexdigest()
        obj_item.wid = obj_item.domain + "_" + obj_item.trans_sha256
        return obj_item
    except Exception as ex:
        # Todo
        print(ex)
        return None


if __name__ == '__main__':
    while True:
        try:
            # 创建连接和队列
            connection_uri =pika.BlockingConnection(parameters=params)
            channel_uri_read = connection_uri.channel()
            # 读取数据
            while True:
                read_item = channel_uri_read.basic_get(queue=ConfigHelper.rabbit_task_queue(), no_ack=False)
                if read_item[2] is None:
                    print("Waiting for new data 5 seconds")
                    time.sleep(5)
                    continue
                domain_result = bytes.decode(read_item[2], encoding="utf-8")
                print('{0} : start process domain --- {1}'.format(datetime.datetime.now(), domain_result))
                domain_obj = get_whois_info(domain_result)
                if domain_obj is not None:
                    # 写入whois
                    print(json.dumps(domain_obj, default=lambda obj: obj.__dict__))
                    channel_uri_read.basic_publish(exchange='amq.direct', routing_key='ConfigHelper.rabbit_result_key()',
                                                   body=json.dumps(domain_obj, default=lambda obj: obj.__dict__),
                                                   properties=pika.BasicProperties(delivery_mode=2))
                channel_uri_read.basic_ack(read_item[0].delivery_tag, False)
                print('{0} : finished process domain --- {1}'.format(datetime.datetime.now(), domain_result))
        except Exception as ex:
            print(ex)
            time.sleep(60)
