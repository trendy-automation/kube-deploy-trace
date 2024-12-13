import re
from typing import List, Dict
import os

def clean_input(input_text: str) -> str:
    # Удаляем строки с командами kubectl
    cleaned_text = re.sub(r"^.*?kubectl\s+.*?$", "", input_text, flags=re.MULTILINE)
    # Убираем строки с заголовками столбцов
    cleaned_text = re.sub(r"^\d{2}:\d{2}\s+NAMESPACE\s+NAME\s+.*?AGE\s*$", "", cleaned_text, flags=re.MULTILINE)
    # Убираем лишние пустые строки
    cleaned_text = re.sub(r"\n\s*\n", "\n", cleaned_text)
    # Оставляем только строки с данными о подах
    valid_lines = []
    for line in cleaned_text.splitlines():
        if re.match(r"^\d{2}:\d{2}\s+\S+\s+\S+\s+\d+/\d+\s+\S+\s+\d+\s+\S+$", line.strip()):
            valid_lines.append(line.strip())
    return "\n".join(valid_lines).strip()

def parse_pod_statuses(input_text: str) -> List[Dict[str, str]]:
    lines = input_text.strip().split("\n")
    headers = ["timestamp", "namespace", "name", "ready", "status", "restarts", "age"]
    pods = []
    for line in lines:
        parts = re.split(r'\s+', line, maxsplit=6)
        if len(parts) == len(headers):
            pod_data = dict(zip(headers, parts))
            pods.append(pod_data)
    return pods

def classify_section(namespace: str, name: str) -> str:
    # Classifying based on namespace and name patterns
    if "cilium" in namespace or "cilium" in name:
        return "cilium"
    if "cert-manager" in namespace or "cert-manager" in name:
        return "cert-manager"
    if "kube-vip" in namespace or "vip" in name:
        return "kube-vip"
    if "kube-system" in namespace and ("etcd" in name or name.startswith("kube-")):
        return "control-plane"
    if "shturval-services" in namespace or "services" in name:
        return "services"
    if "velero" in namespace or "velero" in name:
        return "backup"
    if "trivy" in namespace or "scanner" in name:
        return "security"
    if "snapshotter" in namespace or "snapshot" in name:
        return "snapshot"
    if "kyverno" in namespace or "policy-manager" in name:
        return "policy"
    if "shturval-backend" in namespace or "backend" in name:
        return "backend"
    if "ingress" in namespace or "ingress" in name:
        return "ingress"
    if "shturval-update" in namespace or "update" in name:
        return "update"
    if "shturval-trust" in namespace or "trust" in name:
        return "trust"
    if "shturval-cert-expiration" in namespace or "cert-expiration" in name:
        return "cert-expiration"
    if "coredns" in name:
        return "coredns"
    if "shturval-init-job" in name:
        return "shturval-init-job"
    if "node-config" in namespace:
        return "node-config"
    if "rawfile-provisioner" in namespace:
        return "rawfile-provisioner"
    if "logging" in namespace or "fluent" in name:
        return "logging"
    if "logging" in namespace or "logging" in name:
        return "logging"
    if "shturval-logging" in namespace or "logs-operator" in name:
        return "logging"
    if "monitoring" in namespace or "vmselect" in name or "vminsert" in name:
        return "monitoring"
    if "victoria-metrics" in namespace or "vmagent" in name:
        return "victoria-metrics"
    if "shturval-cluster-manager" in namespace or "cluster-api" in name:
        return "cluster-manager"
    if "shturval-caching" in namespace or "dns" in name:
        return "dns"
    if "shturval-monitoring" in namespace or "monitoring" in name:
        return "monitoring"
    if "capi" in namespace or "controller-manager" in name:
        return "capi"
    if "capv-system" in namespace or "capv-controller-manager" in name:
        return "capv"
    if "capov-system" in namespace or "capov-controller-manager" in name:
        return "capov"
    if "shturval-capsm" in namespace or "capsm-controller-manager" in name:
        return "capsm"
    if "shturval-metrics" in namespace or "metrics-server" in name:
        return "metrics"
    if "get-etcd-cert" in name:
        return "etcd-cert"
    if "vmalertmanager" in name or "alertmanager" in name:
        return "alertmanager"
    if "prometheus" in name or "prometheus" in namespace:
        return "prometheus"
    if "logs" in name or "logs-master" in name:
        return "logs"
    if "caching-dns" in name:
        return "caching-dns"
    if "descheduler" in name:
        return "descheduler"
    if "controller-manager" in name:
        return "controller-manager"
    if "monitoring" in namespace or "monitoring" in name:
        return "monitoring"
    if "cluster-manager" in namespace or "cluster-manager" in name:
        return "cluster-manager"
    if "capv" in namespace or "capv" in name:
        return "capv"
    if "capi" in namespace or "capi" in name:
        return "capi"
    if "capov" in namespace or "capov" in name:
        return "capov"
    print("other", namespace, name)
    return "other"  # Default case if no match

def calculate_start_end(pods: List[Dict[str, str]]) -> List[Dict[str, str]]:
    result = []
    pod_last_seen = {}  # Хранит информацию о последнем состоянии подов
    previous_time = None

    # Начальное время первого события считается за 0
    if pods:
        first_timestamp = pods[0]["timestamp"]
        first_minutes, first_seconds = map(int, first_timestamp.split(":"))
        first_absolute_time = first_minutes * 60 + first_seconds
    else:
        first_absolute_time = 0

    total_elapsed_time = 0  # Общее время, отсчитывающееся по мере переходов

    for pod in pods:
        timestamp = pod.get("timestamp", "00:00")
        minutes, seconds = map(int, timestamp.split(":"))
        current_time = minutes * 60 + seconds

        # Если есть переход с "59:59" на "00:00"
        if previous_time is not None and (total_elapsed_time + current_time - first_absolute_time) < previous_time:
            total_elapsed_time += 3600

        absolute_time = total_elapsed_time + current_time - first_absolute_time
        pod_key = (pod["namespace"], pod["name"])

        # Получение текущего статуса с очисткой
        current_status = re.sub(r':\d+/\d+', '', pod["status"]).replace(':', '')

        # Если под уже был встречен
        if pod_key in pod_last_seen:
            previous_event = pod_last_seen[pod_key]
            # Если статус совпадает, ничего не делаем
            if previous_event["status"] == current_status:
                continue
            else:
                # Закрываем предыдущее событие
                previous_event["end"] = absolute_time

        # Создаем новое событие
        new_event = {
            "name": pod["name"],
            "status": current_status,
            "section": classify_section(pod["namespace"], pod["name"]),
            "start": absolute_time,
            "end": None,  # Пока конец неизвестен
        }
        result.append(new_event)
        pod_last_seen[pod_key] = new_event  # Обновляем последнее состояние для текущего пода

        previous_time = absolute_time

    # Заполняем end для всех подов
    for event in result:
        if event["end"] is None:
            if event["status"] in ["Terminating", "Completed", "Error"]:
                event["end"] = event["start"] + 10  # Для Terminating и Completed
            else:
                event["end"] = previous_time  # Для остальных

    return result

# Имя файла для чтения
input_file = "timeline.log"

# Считываем данные из файла в список
with open(input_file, "r") as file:
    input_text = file.read()

print(f"Данные из {input_file} успешно считаны.")
      
cleaned_text = clean_input(input_text)
parsed_pods = parse_pod_statuses(cleaned_text)
processed_pods = calculate_start_end(parsed_pods)

# Имя файла для сохранения данных
output_file = "processed_pods.txt"

# Открываем файл для записи
script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, output_file), "w") as file:
    # Выводим каждый pod в файл
    for pod in processed_pods:
        file.write(f"{pod},\n")

print(f"Обработанные поды успешно сохранены в файл {output_file}.")