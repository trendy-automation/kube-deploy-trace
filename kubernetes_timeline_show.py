import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
import os

# Имя файла для чтения
input_file = "processed_pods.txt"

# Считываем данные из файла и парсим в список словарей
data = []
script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, input_file), "r") as file:
    for line in file:
        #print(line)
        # Разделяем строку на пары "ключ: значение"
        items = line.strip().strip("{").strip("},").strip("}") .split(",") # Например, если значения через запятую
        parsed_dict = {}
        #print(items)
        for item in items:
            #print(item)
            key, value = item.split(":")  # Разделяем ключ и значение
            key = key.strip().strip("'")
            value = value.strip().strip("'")
            parsed_dict[key] = int(value) if key in ['start','end'] else value
        data.append(parsed_dict)

print("Данные успешно считаны и преобразованы в список словарей.")

# Map statuses to colors
status_colors = {
    "Pending": "orange",
    "Init": "yellow",
    "PodInitializing": "yellow",
    "ContainerCreating": "purple",
    "Running": "green",
    "Completed": "blue",
    "Terminating": "brown",
    "Error": "red",
    "NotReady": "black",
}


# Сортировка данных по секциям и подам
sections = defaultdict(list)
for item in data:
    sections[item["section"]].append(item)

# Упорядочим секции в порядке их первого появления
sorted_sections = sorted(sections.items(), key=lambda x: min(d["start"] for d in x[1]))

# Создаём список уникальных подов в каждой секции
pods_in_sections = []
for section, items in sorted_sections:
    unique_pods = []
    seen_pods = set()
    for item in items:
        if item["name"] not in seen_pods:
            unique_pods.append(item["name"])
            seen_pods.add(item["name"])
    pods_in_sections.extend((section, pod) for pod in unique_pods)

# Создание графика
fig, ax = plt.subplots(figsize=(15, len(pods_in_sections) * 0.6))
bar_height = 0.5

# Словарь для отслеживания y-позиций
pod_y_positions = {pod: i for i, (section, pod) in enumerate(reversed(pods_in_sections))}

# Добавление секций в график
y_labels = []
y_ticks = []
current_section = ""

for (section, pod) in pods_in_sections:
    if section != current_section:
        current_section = section
        y_labels.append(section)
        y_ticks.append(pod_y_positions[pod])

# Рисуем события
for item in data:
    start = item["start"]
    end = item["end"]
    color = status_colors.get(item["status"], "gray")
    y_pos = pod_y_positions[item["name"]]

    ax.barh(
        y_pos,
        width=end - start,
        left=start,
        height=bar_height,
        color=color,
        edgecolor="gray"
    )

# Добавление подписей для подов
for (section, pod) in pods_in_sections:
    ax.text(
        max(item["end"] for item in data if item["name"] == pod) + 5,
        pod_y_positions[pod],
        pod,
        ha="left",
        va="center",
        color="black",
        fontsize=8
    )

# Настройка осей и легенды
max_time = max(item["end"] for item in data) + 120
xticks = range(0, int(max_time) + 60, 60)

ax.set_xticks(xticks)
ax.set_xticklabels([str(tick) for tick in xticks])
ax.grid(True, which="both", axis="x", linestyle="--", linewidth=0.5, color="gray")

ax.set_yticks(y_ticks)
ax.set_yticklabels(y_labels)
ax.set_xlabel("Time (seconds)")
ax.set_title("Kubernetes Cluster Deployment Timeline with Pod Statuses")

ax.legend(
    handles=[mpatches.Patch(color=color, label=status) for status, color in status_colors.items()],
    title="Status",
    loc="upper right"
)

plt.tight_layout()
plt.show()